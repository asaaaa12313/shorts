import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")
TEMP_DIR = BASE_DIR / "temp"
FONTS_DIR = BASE_DIR / "fonts"
BGM_DIR = Path(os.path.expanduser(
    "~/Library/CloudStorage/GoogleDrive-tkfkdgowldms@gmail.com/내 드라이브/3.위즈더플래닝 디자인/숏폼/BGM"
))

# Google Drive 촬영본 폴더
GDRIVE_CLIPS_DIR = Path(os.path.expanduser(
    "~/Library/CloudStorage/GoogleDrive-tkfkdgowldms@gmail.com/내 드라이브/0. 위즈더플래닝 촬영본/0.촬영본"
))

TEMP_DIR.mkdir(exist_ok=True)

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# 영상 설정
TARGET_DURATION = 15.0
WIDTH = 1080
HEIGHT = 1920
FPS = 30

# BGM 볼륨
BGM_VOLUME = 0.45
BGM_FADE_IN = 0.2
BGM_FADE_OUT = 1.0

# TTS 음성이 있을 때 BGM 볼륨
TTS_BGM_VOLUME = 0.15

# Redis / Celery
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# S3 (MVP에서는 로컬 스토리지 사용, 이후 S3로 전환)
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
