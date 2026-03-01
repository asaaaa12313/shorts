"""Google Drive 촬영본 폴더 탐색 - 업체명 검색 및 영상 파일 목록"""
import os
import unicodedata
from pathlib import Path
from app.core.config import GDRIVE_CLIPS_DIR

VIDEO_EXTS = (".mp4", ".MP4", ".mov", ".MOV", ".avi", ".mkv")


def search_businesses(query: str = "") -> list[dict]:
    """업체명 검색. query가 비어있으면 전체 목록 반환"""
    if not GDRIVE_CLIPS_DIR.exists():
        return []

    businesses = []
    for d in sorted(GDRIVE_CLIPS_DIR.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        if query and unicodedata.normalize("NFC", query.lower()) not in unicodedata.normalize("NFC", name.lower()):
            continue
        businesses.append({"name": name, "path": str(d)})

    return businesses


def get_business_clips(business_name: str) -> list[dict]:
    """업체 폴더에서 영상 파일 목록 반환 (하위 폴더 포함)"""
    # macOS NFD 정규화된 폴더명과 매칭
    normalized_name = unicodedata.normalize("NFC", business_name)
    business_dir = None
    for d in GDRIVE_CLIPS_DIR.iterdir():
        if d.is_dir() and unicodedata.normalize("NFC", d.name) == normalized_name:
            business_dir = d
            break
    if business_dir is None:
        return []

    clips = []
    for root, dirs, files in os.walk(str(business_dir)):
        for f in sorted(files):
            if any(f.endswith(ext) for ext in VIDEO_EXTS):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, str(business_dir))
                size_mb = os.path.getsize(full_path) / 1024 / 1024
                clips.append({
                    "filename": f,
                    "path": full_path,
                    "rel_path": rel_path,
                    "size_mb": round(size_mb, 1),
                })

    return clips
