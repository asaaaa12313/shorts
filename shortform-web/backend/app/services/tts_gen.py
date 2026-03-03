"""SRT 자막 → edge-tts 음성 파일 생성"""
import asyncio
import os
import subprocess
import tempfile
import srt
import edge_tts


async def _tts_all_segments(entries, voice: str, rate: str, tmpdir: str) -> list:
    """모든 자막 줄을 한 이벤트 루프에서 순차 변환"""
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


def generate_tts(srt_content: str, output_path: str, duration: float,
                 voice: str = "ko-KR-SunHiNeural",
                 rate: str = "+10%") -> str:
    """
    SRT의 각 자막 줄을 음성으로 변환 → 타이밍에 맞춰 하나의 파일로 합성.
    Returns: output_path (생성된 음성 파일 경로)
    """
    entries = list(srt.parse(srt_content))
    if not entries:
        return ""

    tmpdir = tempfile.mkdtemp(prefix="tts_")

    try:
        # 1. 각 자막 줄을 개별 음성 파일로 변환
        seg_files = _run_async(_tts_all_segments(entries, voice, rate, tmpdir))

        if not seg_files:
            return ""

        # 2. FFmpeg adelay 필터로 각 음성을 시작 시간에 배치 후 amix
        inputs = []
        filter_parts = []
        for idx, (seg_path, start_ms) in enumerate(seg_files):
            inputs.extend(["-i", seg_path])
            filter_parts.append(
                f"[{idx}:a]adelay={start_ms}|{start_ms},apad[a{idx}]"
            )

        # amix로 모든 트랙 합성
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

    finally:
        # 임시 세그먼트 파일 정리
        for f in os.listdir(tmpdir):
            os.remove(os.path.join(tmpdir, f))
        os.rmdir(tmpdir)
