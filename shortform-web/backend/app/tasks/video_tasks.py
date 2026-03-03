"""비동기 영상 처리 파이프라인"""
import os
import shutil
from datetime import datetime
from app.tasks.celery_app import celery_app
from app.core.config import TEMP_DIR, OUTPUT_DIR, TARGET_DURATION
from app.services import video_processor, subtitle_gen, motion_subtitle, bgm_selector, ffmpeg_composer, tts_gen


@celery_app.task(bind=True)
def process_shortform(self, job_id: str, clip_paths: list[str], options: dict) -> dict:
    """
    숏폼 영상 생성 전체 파이프라인.
    options: {
        "business_name": str,
        "bgm_genre": str (optional),
        "bgm_dir": str (optional),
        "subtitle_mode": "ai" | "manual" | "none",
        "subtitle_text": str (manual 모드일 때),
        "business_type": str (업종 - AI 자막 힌트),
        "gemini_api_key": str (optional),
    }
    """
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    try:
        duration = options.get("duration", TARGET_DURATION)

        # 0. 클립 분석 및 선별 (많을 경우 15개로 축소)
        self.update_state(state="PROGRESS", meta={"step": "analyzing", "progress": 5})
        selected_paths = video_processor.select_best_clips(clip_paths, max_clips=15)

        # 1. 클립 결합 (줌 효과 + 전환 효과 포함)
        self.update_state(state="PROGRESS", meta={"step": "combining", "progress": 10})
        combined_path = video_processor.combine_clips(selected_paths, duration, job_id)

        subtitle_mode = options.get("subtitle_mode", "ai")
        srt_content = ""
        srt_path = str(job_dir / "subs.srt")

        if subtitle_mode != "none":
            # 2. 자막 생성
            self.update_state(state="PROGRESS", meta={"step": "subtitles", "progress": 30})

            if subtitle_mode == "manual" and options.get("subtitle_text"):
                srt_content = subtitle_gen.generate_subtitles_from_text(
                    options["subtitle_text"], srt_path, duration
                )
            else:
                srt_content = subtitle_gen.generate_subtitles(
                    combined_path, srt_path,
                    api_key=options.get("gemini_api_key", ""),
                    business_type=options.get("business_type", ""),
                    business_name=options.get("business_name", ""),
                )

        # 2.5. TTS 음성 생성 (자막이 있고 음성 ON일 때)
        tts_path = ""
        if srt_content and options.get("voice_enabled"):
            self.update_state(state="PROGRESS", meta={"step": "tts", "progress": 40})
            tts_path = str(job_dir / "tts.m4a")
            tts_gen.generate_tts(
                srt_content, tts_path, duration,
                voice=options.get("voice_id") or "ko-KR-SunHiNeural",
                engine=options.get("tts_engine", "edge"),
            )

        # 3. BGM 선택
        self.update_state(state="PROGRESS", meta={"step": "bgm", "progress": 50})
        filenames = [os.path.basename(p) for p in clip_paths]
        bgm_info = bgm_selector.select_bgm(
            srt_content=srt_content,
            filenames=filenames,
            genre=options.get("bgm_genre", ""),
            bgm_dir=options.get("bgm_dir", ""),
        )

        # 4. 모션 자막 프레임 생성 (자막이 있을 때만)
        frames_dir = ""
        if srt_content:
            self.update_state(state="PROGRESS", meta={"step": "motion_frames", "progress": 60})
            frames_dir = str(job_dir / "frames")
            motion_subtitle.generate_frames(
                srt_content, duration, frames_dir,
                effect=options.get("subtitle_effect", ""),
                color_scheme=options.get("subtitle_color", ""),
            )

        # 5. FFmpeg 합성
        self.update_state(state="PROGRESS", meta={"step": "composing", "progress": 85})
        business_name = options.get("business_name", "output")
        date_str = datetime.now().strftime("%Y%m%d")
        suffix = "_nosub" if subtitle_mode == "none" else ""
        filename = f"shortform_{date_str}_{business_name}{suffix}.mp4"
        output_path = str(OUTPUT_DIR / filename)

        ffmpeg_composer.compose(
            video_path=combined_path,
            frames_dir=frames_dir,
            bgm_path=bgm_info.get("path", ""),
            output_path=output_path,
            duration=duration,
            tts_path=tts_path,
        )

        # 6. 임시 파일 정리
        self.update_state(state="PROGRESS", meta={"step": "cleanup", "progress": 95})
        shutil.rmtree(job_dir, ignore_errors=True)

        return {
            "status": "completed",
            "progress": 100,
            "filename": filename,
            "output_path": output_path,
            "bgm_genre": bgm_info.get("genre", ""),
            "bgm_filename": bgm_info.get("filename", ""),
        }

    except Exception:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise


@celery_app.task(bind=True)
def process_add_subtitle(self, video_path: str, subtitle_text: str, business_name: str, subtitle_effect: str = "", subtitle_color: str = "", voice_enabled: bool = False, voice_id: str = "", tts_engine: str = "edge") -> dict:
    """기존 영상에 자막만 입히기"""
    import uuid
    job_id = str(uuid.uuid4())[:8]
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    try:
        # 1. 영상 길이 파악
        self.update_state(state="PROGRESS", meta={"step": "subtitles", "progress": 20})
        import subprocess, json
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", video_path],
            capture_output=True, text=True
        )
        duration = float(json.loads(probe.stdout)["format"]["duration"])

        # 2. SRT 생성
        srt_path = str(job_dir / "subs.srt")
        srt_content = subtitle_gen.generate_subtitles_from_text(
            subtitle_text, srt_path, duration
        )

        # 3. 모션 자막 프레임
        self.update_state(state="PROGRESS", meta={"step": "motion_frames", "progress": 50})
        frames_dir = str(job_dir / "frames")
        motion_subtitle.generate_frames(srt_content, duration, frames_dir,
                                        effect=subtitle_effect, color_scheme=subtitle_color)

        # 3.5. TTS 음성 생성
        tts_path = ""
        if voice_enabled:
            self.update_state(state="PROGRESS", meta={"step": "tts", "progress": 65})
            tts_path = str(job_dir / "tts.m4a")
            tts_gen.generate_tts(
                srt_content, tts_path, duration,
                voice=voice_id or "ko-KR-SunHiNeural",
                engine=tts_engine,
            )

        # 4. 합성 (자막 + TTS 오버레이)
        self.update_state(state="PROGRESS", meta={"step": "composing", "progress": 80})
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"shortform_{date_str}_{business_name}_sub.mp4"
        output_path = str(OUTPUT_DIR / filename)

        ffmpeg_composer.compose(
            video_path=video_path,
            frames_dir=frames_dir,
            bgm_path="",
            output_path=output_path,
            duration=duration,
            tts_path=tts_path,
        )

        # 5. 정리
        self.update_state(state="PROGRESS", meta={"step": "cleanup", "progress": 95})
        shutil.rmtree(job_dir, ignore_errors=True)

        return {
            "status": "completed",
            "progress": 100,
            "filename": filename,
        }

    except Exception as e:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise
