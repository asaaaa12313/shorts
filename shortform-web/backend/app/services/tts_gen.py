"""SRT 자막 → edge-tts / ElevenLabs 음성 파일 생성"""
import asyncio
import os
import subprocess
import tempfile
import srt
import edge_tts

from app.core.config import ELEVENLABS_API_KEY


# ========== edge-tts ==========

async def _edge_tts_segments(entries, voice: str, tmpdir: str) -> list:
    """edge-tts: 피치/속도 조절로 발랄한 톤 적용"""
    seg_files = []
    for i, entry in enumerate(entries):
        text = entry.content.replace("\n", " ").strip()
        if not text:
            continue
        seg_path = os.path.join(tmpdir, f"seg_{i:03d}.mp3")

        # 첫 번째 자막: 밝고 높은 톤 (후킹) - 신나게
        # 마지막 자막: 강조하되 업된 톤 유지 (CTA)
        # 중간: 밝고 활기찬 톤
        if i == 0:
            pitch, seg_rate = "+20Hz", "+15%"
        elif i == len(entries) - 1:
            pitch, seg_rate = "+8Hz", "-3%"
        else:
            pitch, seg_rate = "+12Hz", "+5%"

        communicate = edge_tts.Communicate(text, voice=voice, rate=seg_rate, pitch=pitch)
        await communicate.save(seg_path)
        start_ms = int(entry.start.total_seconds() * 1000)
        seg_files.append((seg_path, start_ms))
    return seg_files


def _run_async(coro):
    """Celery 데몬 프로세스에서도 안전하게 async 실행"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ========== ElevenLabs ==========

def _elevenlabs_segments(entries, voice_id: str, tmpdir: str) -> list:
    """ElevenLabs: 각 자막 줄을 음성으로 변환"""
    from elevenlabs import ElevenLabs

    api_key = ELEVENLABS_API_KEY
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY가 설정되지 않았습니다. .env 파일에 추가해주세요.")

    client = ElevenLabs(api_key=api_key)
    seg_files = []

    for i, entry in enumerate(entries):
        text = entry.content.replace("\n", " ").strip()
        if not text:
            continue
        seg_path = os.path.join(tmpdir, f"seg_{i:03d}.mp3")

        audio = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
            voice_settings={
                "stability": 0.2,           # 낮을수록 감정 표현 풍부
                "similarity_boost": 0.75,    # 음색 일관성
                "style": 0.9,               # 스타일 표현력 (발랄함 극대화)
                "use_speaker_boost": True,
            },
        )

        with open(seg_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        start_ms = int(entry.start.total_seconds() * 1000)
        seg_files.append((seg_path, start_ms))

    return seg_files


# ========== 공통 합성 ==========

def _get_audio_duration(path: str) -> float:
    """MP3 파일의 실제 재생 시간(초)"""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, timeout=10,
    )
    try:
        return float(result.stdout.strip())
    except (ValueError, AttributeError):
        return 3.0  # fallback


def _mix_segments(seg_files: list, duration: float, output_path: str) -> str:
    """개별 음성 세그먼트 → 길면 atempo로 속도 조절 후 합성 (겹침 방지)"""
    inputs = []
    filter_parts = []
    for idx, (seg_path, start_ms) in enumerate(seg_files):
        inputs.extend(["-i", seg_path])

        filters = []
        # 다음 세그먼트까지 사용 가능한 시간 계산
        if idx + 1 < len(seg_files):
            next_start_ms = seg_files[idx + 1][1]
            window_sec = max((next_start_ms - start_ms - 100) / 1000.0, 0.5)
        else:
            window_sec = max(duration - start_ms / 1000.0, 0.5)

        # 실제 음성 길이 측정 → 길면 atempo로 빠르게
        seg_dur = _get_audio_duration(seg_path)
        if seg_dur > window_sec:
            tempo = min(seg_dur / window_sec, 1.8)  # 최대 1.8배속
            if tempo > 1.05:  # 5% 이상 차이날 때만 적용
                filters.append(f"atempo={tempo:.2f}")

        filters.append(f"adelay={start_ms}|{start_ms}")
        filters.append("apad")
        filter_parts.append(f"[{idx}:a]{','.join(filters)}[a{idx}]")

    mix_inputs = "".join(f"[a{i}]" for i in range(len(seg_files)))
    filter_parts.append(
        f"{mix_inputs}amix=inputs={len(seg_files)}:duration=longest,"
        f"atrim=0:{duration},"
        f"equalizer=f=5000:t=h:width_type=h:width=2000:g=3,"
        f"aformat=sample_rates=44100:channel_layouts=mono[out]"
    )

    filter_str = ";\n".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[out]",
        "-c:a", "aac", "-b:a", "128k",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"TTS 합성 실패: {result.stderr[-500:]}")

    return output_path


# ========== 진입점 ==========

def generate_tts(srt_content: str, output_path: str, duration: float,
                 voice: str = "ko-KR-SunHiNeural",
                 engine: str = "edge") -> str:
    """
    SRT의 각 자막 줄을 음성으로 변환 → 타이밍에 맞춰 하나의 파일로 합성.
    engine: "edge" (무료, edge-tts) | "elevenlabs" (프리미엄)
    """
    entries = list(srt.parse(srt_content))
    if not entries:
        return ""

    tmpdir = tempfile.mkdtemp(prefix="tts_")

    try:
        if engine == "elevenlabs":
            try:
                seg_files = _elevenlabs_segments(entries, voice, tmpdir)
            except Exception as e:
                err_msg = str(e)
                if "402" in err_msg or "payment_required" in err_msg or "paid_plan" in err_msg:
                    print(f"[TTS] ElevenLabs 유료 플랜 필요 - edge_tts로 자동 전환: {err_msg}")
                    seg_files = _run_async(
                        _edge_tts_segments(entries, "ko-KR-SunHiNeural", tmpdir)
                    )
                else:
                    raise
        else:
            seg_files = _run_async(_edge_tts_segments(entries, voice, tmpdir))

        if not seg_files:
            return ""

        return _mix_segments(seg_files, duration, output_path)

    finally:
        for f in os.listdir(tmpdir):
            os.remove(os.path.join(tmpdir, f))
        os.rmdir(tmpdir)
