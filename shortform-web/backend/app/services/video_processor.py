"""클립 분석, 선별, 줌 효과, 전환 효과, 결합"""
import json
import os
import random
import subprocess
from pathlib import Path
from app.core.config import WIDTH, HEIGHT, FPS, TARGET_DURATION, TEMP_DIR


# --- 전환 효과 ---
TRANSITIONS = [
    "fade", "slideright", "slideleft", "slideup", "slidedown",
    "circlecrop", "dissolve", "smoothleft", "smoothright", "fadeblack",
]
TRANSITION_DURATION = 0.4  # 초
MIN_CLIP_DURATION = 2.5  # 클립 최소 표시 시간 (초)

# --- 줌 효과 ---
ZOOM_AMOUNT = 0.08  # 8%


def _probe_clip(path: str) -> dict:
    """ffprobe로 클립 정보 반환"""
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", path],
            capture_output=True, text=True, timeout=10
        )
        info = json.loads(probe.stdout)
        duration = float(info.get("format", {}).get("duration", 0))
        vs = next((s for s in info.get("streams", []) if s["codec_type"] == "video"), {})
        return {
            "path": path,
            "filename": os.path.basename(path),
            "duration": duration,
            "width": int(vs.get("width", 0)),
            "height": int(vs.get("height", 0)),
            "size": os.path.getsize(path),
        }
    except Exception:
        return {"path": path, "filename": os.path.basename(path),
                "duration": 0, "width": 0, "height": 0, "size": 0}


def select_best_clips(clip_paths: list[str], max_clips: int = 15) -> list[str]:
    """클립들을 분석하여 최적의 max_clips개를 선별. max_clips 이하면 전부 반환."""
    if len(clip_paths) <= max_clips:
        return clip_paths

    analyzed = []
    for path in clip_paths:
        info = _probe_clip(path)
        if info["duration"] < 0.5:  # 0.5초 미만 건너뜀
            continue
        # 점수: 해상도(30%) + 길이(40%) + 파일크기=화질(30%)
        res_score = min(info["width"] * info["height"] / (1920 * 1080), 1.0)
        dur_score = min(info["duration"] / 5.0, 1.0)
        size_score = min(info["size"] / (50 * 1024 * 1024), 1.0)
        info["score"] = res_score * 0.3 + dur_score * 0.4 + size_score * 0.3
        analyzed.append(info)

    if len(analyzed) <= max_clips:
        return [c["path"] for c in analyzed]

    # 점수 상위 70%에서 균등 샘플링 (다양성 확보)
    analyzed.sort(key=lambda x: x["score"], reverse=True)
    pool = analyzed[:max(max_clips, int(len(analyzed) * 0.7))]
    step = len(pool) / max_clips
    selected = [pool[int(i * step)] for i in range(max_clips)]

    # 원래 순서 유지
    order = {p: i for i, p in enumerate(clip_paths)}
    selected.sort(key=lambda x: order.get(x["path"], 0))
    return [c["path"] for c in selected]


def _zoom_filter(effect: str, duration: float) -> str:
    """줌 효과 필터 문자열 생성"""
    z = ZOOM_AMOUNT
    if effect == "zoom_in":
        return (
            f"scale=w='trunc(({WIDTH}*(1+{z}*t/{duration}))/2)*2'"
            f":h='trunc(({HEIGHT}*(1+{z}*t/{duration}))/2)*2'"
            f":eval=frame,crop={WIDTH}:{HEIGHT}"
        )
    elif effect == "zoom_out":
        return (
            f"scale=w='trunc(({WIDTH}*(1+{z}-{z}*t/{duration}))/2)*2'"
            f":h='trunc(({HEIGHT}*(1+{z}-{z}*t/{duration}))/2)*2'"
            f":eval=frame,crop={WIDTH}:{HEIGHT}"
        )
    return ""


def _process_single_clip(path: str, index: int, clip_duration: float,
                          job_dir: Path, zoom_effect: str) -> str:
    """단일 클립: 리사이즈 + 트림 + 줌 효과. 오디오 제거 (BGM으로 대체)."""
    out = str(job_dir / f"clip_{index}.mp4")
    info = _probe_clip(path)
    orig_w, orig_h = info["width"] or 1920, info["height"] or 1080
    orig_dur = info["duration"] or 10.0

    trim_margin = min(1.0, orig_dur * 0.1)
    start = trim_margin
    max_usable = orig_dur - trim_margin * 2  # 앞뒤 1초씩 제외
    duration = min(clip_duration, max(max_usable, orig_dur * 0.5))  # 최소 50%는 사용

    zoom_f = _zoom_filter(zoom_effect, duration)

    if orig_w > orig_h:
        # 가로 영상 → 블러 배경 + 중앙 배치
        vf = (
            f"[0:v]split=2[bg][fg];"
            f"[bg]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},boxblur=20:5[bgout];"
            f"[fg]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black@0[fgout];"
            f"[bgout][fgout]overlay=0:0"
        )
        if zoom_f:
            vf += f",{zoom_f}"
        cmd = [
            "ffmpeg", "-y", "-ss", str(start), "-i", path,
            "-t", str(duration),
            "-filter_complex", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an", "-r", str(FPS), out
        ]
    else:
        # 세로 영상
        vf = (f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
              f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black")
        if zoom_f:
            vf += f",{zoom_f}"
        cmd = [
            "ffmpeg", "-y", "-ss", str(start), "-i", path,
            "-t", str(duration), "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an", "-r", str(FPS), out
        ]

    subprocess.run(cmd, capture_output=True, check=True)
    return out


def combine_clips(clip_paths: list[str], target_duration: float = TARGET_DURATION,
                   job_id: str = "job") -> str:
    """여러 클립을 1080x1920 세로 영상으로 결합 (줌 효과 + 전환 효과 포함)"""
    if not clip_paths:
        raise ValueError("클립이 없습니다")

    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    n = len(clip_paths)

    # 클립 최소 길이 보장: 클립이 너무 많으면 줄이기
    max_clips = max(1, int(target_duration / MIN_CLIP_DURATION))
    if n > max_clips:
        step = len(clip_paths) / max_clips
        clip_paths = [clip_paths[int(i * step)] for i in range(max_clips)]
        n = len(clip_paths)

    use_transitions = n >= 2
    td = TRANSITION_DURATION if use_transitions else 0

    # 전환 겹침을 감안한 클립당 길이
    clip_duration = (target_duration + (n - 1) * td) / n if use_transitions else target_duration / n

    # 줌 효과 랜덤 할당 (zoom_in ↔ zoom_out 교대 + 간헐적 없음)
    zoom_effects = []
    for i in range(n):
        if random.random() < 0.2:
            zoom_effects.append("none")
        else:
            zoom_effects.append("zoom_in" if i % 2 == 0 else "zoom_out")

    # 1. 개별 클립 처리
    processed = []
    for i, path in enumerate(clip_paths):
        out = _process_single_clip(path, i, clip_duration, job_dir, zoom_effects[i])
        processed.append(out)

    combined_path = str(job_dir / "combined.mp4")

    if not use_transitions or n == 1:
        # 단일 클립이면 그대로 복사
        import shutil
        shutil.copy2(processed[0], combined_path)
        return combined_path

    # 2. xfade 전환 효과로 결합
    cmd = ["ffmpeg", "-y"]
    for p in processed:
        cmd.extend(["-i", p])

    # 전환 종류 셔플
    trans_list = TRANSITIONS.copy()
    random.shuffle(trans_list)

    # 비디오: xfade 체인
    vfilters = []
    for i in range(n - 1):
        in1 = f"[{i}:v]" if i == 0 else f"[v{i}]"
        in2 = f"[{i + 1}:v]"
        is_last = i == n - 2
        out_label = "[xout]" if is_last else f"[v{i + 1}]"
        t = trans_list[i % len(trans_list)]
        offset = round((i + 1) * (clip_duration - td), 3)
        vfilters.append(
            f"{in1}{in2}xfade=transition={t}:duration={td}:offset={offset}{out_label}"
        )
    # xfade 체인 후 PTS를 0부터 시작하도록 리셋
    vfilters.append("[xout]setpts=PTS-STARTPTS[vout]")

    filter_complex = ";\n".join(vfilters)

    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-r", str(FPS),
        "-t", str(target_duration),
        "-an",
        combined_path
    ])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"xfade 합성 실패: {result.stderr[-500:]}")

    return combined_path


def analyze_clips(clip_dir: str) -> list[dict]:
    """클립 폴더를 스캔하여 파일 정보 반환"""
    extensions = ("*.mp4", "*.MP4", "*.mov", "*.MOV", "*.avi", "*.mkv")
    import glob
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(clip_dir, ext)))
    files.sort()
    return [_probe_clip(f) for f in files]
