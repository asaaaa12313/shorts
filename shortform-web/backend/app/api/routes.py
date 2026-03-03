"""API 엔드포인트"""
import uuid
import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.core.config import UPLOAD_DIR, OUTPUT_DIR
from app.tasks.video_tasks import process_shortform, process_add_subtitle
from app.tasks.celery_app import celery_app
from app.services.bgm_selector import list_genres
from app.services.gdrive_browser import search_businesses, get_business_clips

router = APIRouter(prefix="/api")


class GenerateRequest(BaseModel):
    job_id: str = ""
    business_name: str = "output"
    bgm_genre: str = ""
    bgm_dir: str = ""
    subtitle_mode: str = "ai"  # "ai" | "manual" | "none"
    subtitle_text: str = ""
    business_type: str = ""  # 업종 (카페, 음식점, 골프 등)
    gemini_api_key: str = ""
    subtitle_effect: str = ""  # 자막 효과
    subtitle_color: str = ""   # 자막 색상 (neon, warm, cool, pastel, rainbow, gold, pink, mint)
    voice_enabled: bool = False  # AI 음성 나레이션 ON/OFF
    voice_id: str = ""  # 음성 ID (ko-KR-SunHiNeural 등)
    tts_engine: str = "edge"  # "edge" (무료) | "elevenlabs" (프리미엄)
    # Google Drive에서 직접 가져올 때
    gdrive_business: str = ""
    gdrive_clip_paths: list[str] = []


class AddSubtitleRequest(BaseModel):
    video_filename: str  # output/에 있는 영상 파일명
    subtitle_text: str
    business_name: str = "output"
    subtitle_effect: str = ""
    subtitle_color: str = ""
    voice_enabled: bool = False
    voice_id: str = ""
    tts_engine: str = "edge"


class JobStatus(BaseModel):
    job_id: str
    status: str
    step: str = ""
    progress: int = 0
    filename: str = ""
    error: str = ""
    bgm_genre: str = ""
    bgm_filename: str = ""


# --- Google Drive 업체 검색 ---

@router.get("/drive/search")
async def drive_search(q: str = ""):
    """Google Drive 촬영본 업체명 검색"""
    businesses = search_businesses(q)
    return {"businesses": businesses, "count": len(businesses)}


@router.get("/drive/clips/{business_name:path}")
async def drive_clips(business_name: str):
    """업체 폴더의 영상 파일 목록"""
    clips = get_business_clips(business_name)
    return {"business": business_name, "clips": clips, "count": len(clips)}


# --- 파일 업로드 ---

@router.post("/upload")
async def upload_clips(files: list[UploadFile] = File(...)):
    """영상 클립 업로드 → job_id 반환"""
    job_id = str(uuid.uuid4())[:8]
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for i, file in enumerate(files):
        filename = f"{i:02d}_{file.filename}"
        filepath = str(job_dir / filename)
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
        saved_files.append({"filename": filename, "path": filepath})

    return {"job_id": job_id, "files": saved_files, "count": len(saved_files)}


# --- 숏폼 생성 ---

@router.post("/generate")
async def generate_shortform(req: GenerateRequest):
    """숏폼 생성 요청 → Celery 작업 시작"""

    # 클립 경로 결정: Google Drive vs 업로드
    if req.gdrive_clip_paths:
        clip_paths = req.gdrive_clip_paths
        job_id = req.job_id or str(uuid.uuid4())[:8]
    elif req.gdrive_business:
        clips = get_business_clips(req.gdrive_business)
        if not clips:
            raise HTTPException(status_code=404, detail=f"'{req.gdrive_business}' 폴더에 영상이 없습니다")
        clip_paths = [c["path"] for c in clips]
        job_id = req.job_id or str(uuid.uuid4())[:8]
    else:
        job_id = req.job_id
        if not job_id:
            raise HTTPException(status_code=400, detail="job_id 또는 gdrive_business가 필요합니다")
        job_dir = UPLOAD_DIR / job_id
        if not job_dir.exists():
            raise HTTPException(status_code=404, detail="업로드된 파일을 찾을 수 없습니다")
        clip_paths = sorted([
            str(f) for f in job_dir.iterdir()
            if f.suffix.lower() in (".mp4", ".mov", ".avi", ".mkv")
        ])

    if not clip_paths:
        raise HTTPException(status_code=400, detail="영상 파일이 없습니다")

    options = {
        "business_name": req.business_name or req.gdrive_business or "output",
        "bgm_genre": req.bgm_genre,
        "bgm_dir": req.bgm_dir,
        "subtitle_mode": req.subtitle_mode,
        "subtitle_text": req.subtitle_text,
        "business_type": req.business_type,
        "gemini_api_key": req.gemini_api_key,
        "subtitle_effect": req.subtitle_effect,
        "subtitle_color": req.subtitle_color,
        "voice_enabled": req.voice_enabled,
        "voice_id": req.voice_id,
        "tts_engine": req.tts_engine,
    }

    task = process_shortform.delay(job_id, clip_paths, options)

    return {"job_id": job_id, "task_id": task.id, "status": "started"}


# --- 자막 나중에 입히기 ---

@router.post("/add-subtitle")
async def add_subtitle(req: AddSubtitleRequest):
    """기존 영상에 자막만 입히기"""
    filepath = OUTPUT_DIR / req.video_filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="영상 파일을 찾을 수 없습니다")

    task = process_add_subtitle.delay(
        str(filepath), req.subtitle_text, req.business_name,
        req.subtitle_effect, req.subtitle_color,
        req.voice_enabled, req.voice_id, req.tts_engine,
    )
    return {"task_id": task.id, "status": "started"}


# --- 상태 조회 ---

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    """작업 상태 조회"""
    result = celery_app.AsyncResult(task_id)

    if result.state == "PENDING":
        return JobStatus(job_id="", status="pending", progress=0)
    elif result.state == "PROGRESS":
        info = result.info or {}
        return JobStatus(
            job_id="", status="processing",
            step=info.get("step", ""),
            progress=info.get("progress", 0),
        )
    elif result.state == "SUCCESS":
        info = result.result or {}
        return JobStatus(
            job_id="", status="completed",
            progress=100,
            filename=info.get("filename", ""),
            bgm_genre=info.get("bgm_genre", ""),
            bgm_filename=info.get("bgm_filename", ""),
        )
    elif result.state == "FAILURE":
        return JobStatus(
            job_id="", status="failed",
            error=str(result.info) if result.info else "알 수 없는 오류",
        )

    return JobStatus(job_id="", status=result.state.lower(), progress=0)


# --- 다운로드 ---

@router.get("/download/{filename}")
async def download_file(filename: str):
    """완성된 영상 다운로드"""
    filepath = OUTPUT_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    return FileResponse(str(filepath), media_type="video/mp4", filename=filename)


@router.get("/output/list")
async def list_output():
    """완성된 영상 목록 (자막 입히기용)"""
    files = []
    if OUTPUT_DIR.exists():
        for f in sorted(OUTPUT_DIR.iterdir(), reverse=True):
            if f.suffix.lower() == ".mp4":
                stat = f.stat()
                size_mb = stat.st_size / 1024 / 1024
                created = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                files.append({"filename": f.name, "size_mb": round(size_mb, 1), "created_at": created})
    return {"files": files}


# --- BGM ---

@router.get("/bgm/genres")
async def get_bgm_genres(bgm_dir: str = ""):
    """BGM 장르 목록"""
    return {"genres": list_genres(bgm_dir)}
