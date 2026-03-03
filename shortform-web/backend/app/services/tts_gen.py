"""SRT 자막 → edge-tts / ElevenLabs 음성 파일 생성"""
import asyncio
import os
import subprocess
import tempfile
import srt
import edge_tts

from app.core.config import ELEVENLABS_API_KEY


# ========== edge-tts ==========

async def _edge_tts_segments(entries, voice: str, rate: str, tmpdir: str) -> list:
    """edge-tts: 모든 자막 줄을 순차 변환"""
    seg_files = []
    for i, entry in enumerate(entries):
        text = entry.content.replace("\n", " ").strip()
        if not text:
            continue
        seg_path = os.path.join(tmpdir, f"seg_{i:03d}.mp3")
        communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
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
        )

        with open(seg_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        start_ms = int(entry.start.total_seconds() * 1000)
        seg_files.append((seg_path, start_ms))

    return seg_files


# ========== 공통 합성 ==========

def _mix_segments(seg_files: list, duration: float, output_path: str) -> str:
    """개별 음성 세그먼트 → FFmpeg adelay + amix로 합성"""
    inputs = []
    filter_parts = []
    for idx, (seg_path, start_ms) in enumerate(seg_files):
        inputs.extend(["-i", seg_path])
        filter_parts.append(
            f"[{idx}:a]adelay={start_ms}|{start_ms},apad[a{idx}]"
        )

    mix_inputs = "".join(f"[a{i}]" for i in range(len(seg_files)))
    filter_parts.append(
        f"{mix_inputs}amix=inputs={len(seg_files)}:duration=longest,"
        f"atrim=0:{duration},aformat=sample_rates=44100:channel_layouts=mono[out]"
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
                 rate: str = "-5%",
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
            seg_files = _elevenlabs_segments(entries, voice, tmpdir)
        else:
            seg_files = _run_async(_edge_tts_segments(entries, voice, rate, tmpdir))

        if not seg_files:
            return ""

        return _mix_segments(seg_files, duration, output_path)

    finally:
        for f in os.listdir(tmpdir):
            os.remove(os.path.join(tmpdir, f))
        os.rmdir(tmpdir)
