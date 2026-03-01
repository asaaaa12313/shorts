"""FFmpeg로 영상 + 모션 자막 프레임 + BGM + TTS 합성"""
import json
import subprocess
from app.core.config import FPS, BGM_VOLUME, BGM_FADE_IN, BGM_FADE_OUT, TTS_BGM_VOLUME


def _has_audio(video_path: str) -> bool:
    """비디오 파일에 오디오 스트림이 있는지 확인"""
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", video_path],
            capture_output=True, text=True, timeout=10
        )
        info = json.loads(probe.stdout)
        return any(s.get("codec_type") == "audio" for s in info.get("streams", []))
    except Exception:
        return False


def compose(video_path: str, frames_dir: str, bgm_path: str,
            output_path: str, duration: float = 15.0,
            tts_path: str = "") -> str:
    """영상 + 자막 프레임 오버레이 + BGM + TTS 믹스 → 최종 MP4"""

    has_frames = bool(frames_dir)
    has_bgm = bool(bgm_path)
    has_tts = bool(tts_path)
    source_has_audio = _has_audio(video_path)

    cmd = ["ffmpeg", "-y", "-i", video_path]

    # 자막 프레임이 있으면 입력 추가
    if has_frames:
        cmd.extend(["-framerate", str(FPS), "-i", f"{frames_dir}/frame_%04d.png"])

    # 다음 입력 인덱스 계산
    next_idx = 2 if has_frames else 1

    bgm_idx = None
    if has_bgm:
        cmd.extend(["-i", bgm_path])
        bgm_idx = next_idx
        next_idx += 1

    tts_idx = None
    if has_tts:
        cmd.extend(["-i", tts_path])
        tts_idx = next_idx
        next_idx += 1

    filter_parts = []

    # TTS가 있으면 BGM 볼륨을 낮춤
    bgm_vol = TTS_BGM_VOLUME if has_tts else BGM_VOLUME

    # BGM 오디오 필터
    if has_bgm:
        filter_parts.append(
            f"[{bgm_idx}:a]atrim=0:{duration},"
            f"afade=t=in:st=0:d={BGM_FADE_IN},"
            f"afade=t=out:st={duration - BGM_FADE_OUT}:d={BGM_FADE_OUT},"
            f"volume={bgm_vol}[bgm]"
        )

    # TTS 오디오 필터
    if has_tts:
        filter_parts.append(f"[{tts_idx}:a]volume=0.9[tts]")

    # 오디오 믹싱
    if has_bgm and has_tts:
        filter_parts.append("[bgm][tts]amix=inputs=2:duration=first[aout]")
        audio_map = ["-map", "[aout]"]
    elif has_bgm and not has_tts:
        if source_has_audio:
            filter_parts.append("[0:a][bgm]amix=inputs=2:duration=first[aout]")
            audio_map = ["-map", "[aout]"]
        else:
            audio_map = ["-map", "[bgm]"]
    elif has_tts and not has_bgm:
        audio_map = ["-map", "[tts]"]
    else:
        audio_map = ["-map", "0:a?"]

    # 비디오 필터
    if has_frames:
        filter_parts.append("[0:v][1:v]overlay=0:0:shortest=1[vout]")
        video_map = ["-map", "[vout]"]
    else:
        video_map = ["-map", "0:v"]

    if filter_parts:
        cmd.extend(["-filter_complex", ";\n".join(filter_parts)])

    cmd.extend([
        *video_map,
        *audio_map,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", str(FPS),
        "-t", str(duration),
        "-movflags", "+faststart",
        output_path
    ])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg 합성 실패: {result.stderr[-500:]}")

    return output_path
