#!/bin/bash
# ============================================
# 숏폼 자동 생성 프로젝트 - 초기 세팅 스크립트
# ============================================
# 사용법: bash setup.sh
# ============================================

# Homebrew PATH 로드 (Apple Silicon Mac)
if [ -f /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
elif [ -f /usr/local/bin/brew ]; then
    eval "$(/usr/local/bin/brew shellenv)"
fi

echo "================================================"
echo "  숏폼 자동 생성 프로젝트 - 초기 세팅 시작"
echo "================================================"
echo ""

# 1. 프로젝트 폴더 구조 생성
echo "[1/5] 프로젝트 폴더 구조 생성 중..."
mkdir -p raw_clips
mkdir -p bgm
mkdir -p fonts
mkdir -p output/reels
mkdir -p output/shorts
mkdir -p output/tiktok
mkdir -p temp
mkdir -p scripts
echo "  ✅ 폴더 구조 생성 완료"
echo ""

# 2. FFmpeg 설치 확인
echo "[2/5] FFmpeg 설치 확인..."
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VER=$(ffmpeg -version | head -1)
    echo "  ✅ FFmpeg 설치됨: $FFMPEG_VER"
else
    echo "  ❌ FFmpeg가 설치되어 있지 않습니다."
    echo "  → 설치 명령어: brew install ffmpeg"
    echo "  → 설치 후 이 스크립트를 다시 실행해주세요."
fi
echo ""

# 3. Python 및 pip 확인
echo "[3/5] Python 환경 확인..."
if command -v python3 &> /dev/null; then
    PY_VER=$(python3 --version)
    echo "  ✅ Python 설치됨: $PY_VER"
else
    echo "  ❌ Python3가 설치되어 있지 않습니다."
    echo "  → 설치 명령어: brew install python3"
fi
echo ""

# 4. Python 패키지 설치
echo "[4/5] Python 패키지 설치 중..."
pip3 install --quiet google-genai python-dotenv moviepy pydub srt Pillow 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✅ Python 패키지 설치 완료 (google-genai, dotenv, moviepy, pydub, srt, Pillow)"
else
    echo "  ⚠️  일부 패키지 설치 실패. 아래 명령어로 수동 설치해주세요:"
    echo "  → pip3 install google-genai python-dotenv moviepy pydub srt Pillow"
fi
echo ""

# 5. 한글 폰트 다운로드 (나눔스퀘어)
echo "[5/5] 한글 폰트 확인..."
if [ -f "fonts/NanumSquareB.ttf" ]; then
    echo "  ✅ 한글 폰트 이미 존재"
else
    echo "  📥 나눔스퀘어 폰트 다운로드 중..."
    curl -sL "https://hangeul.naver.com/hangeul_static/webfont/zips/NanumSquare.zip" -o temp/NanumSquare.zip 2>/dev/null
    if [ $? -eq 0 ] && [ -s "temp/NanumSquare.zip" ]; then
        unzip -qo temp/NanumSquare.zip -d temp/NanumSquare 2>/dev/null
        # 볼드 폰트 찾아서 복사
        find temp/NanumSquare -name "*Bold*" -name "*.ttf" 2>/dev/null | head -1 | xargs -I{} cp {} fonts/NanumSquareB.ttf 2>/dev/null
        rm -rf temp/NanumSquare temp/NanumSquare.zip
    fi
    # 다운로드 실패 시 시스템에 설치된 한글 폰트 검색
    if [ ! -f "fonts/NanumSquareB.ttf" ]; then
        echo "  ℹ️  다운로드 실패. 시스템 한글 폰트 검색 중..."
        SYS_FONT=$(find /System/Library/Fonts /Library/Fonts ~/Library/Fonts -name "*.ttf" -o -name "*.otf" 2>/dev/null | grep -iE "nanum|pretendard|noto.*cjk|apple.*gothic|malgun" | head -1)
        if [ -n "$SYS_FONT" ]; then
            cp "$SYS_FONT" fonts/NanumSquareB.ttf
            echo "  ✅ 시스템 폰트 복사 완료: $(basename "$SYS_FONT")"
        else
            echo "  ⚠️  한글 폰트를 찾을 수 없습니다."
            echo "  → fonts/ 폴더에 한글 .ttf 폰트 파일을 직접 넣어주세요."
            echo "  → 추천: 나눔스퀘어, 프리텐다드, 노토산스 등"
        fi
    else
        echo "  ✅ 한글 폰트 다운로드 완료"
    fi
fi
echo ""

# 완료 메시지
echo "================================================"
echo "  초기 세팅 완료!"
echo "================================================"
echo ""
echo "📁 프로젝트 구조:"
echo "  raw_clips/  ← 촬영한 영상 클립들을 여기에 넣으세요"
echo "  bgm/        ← 배경음악 파일을 여기에 넣으세요"
echo "  fonts/      ← 한글 폰트 파일 (.ttf)"
echo "  output/     ← 완성된 숏폼이 여기에 저장됩니다"
echo ""
echo "🚀 다음 단계:"
echo "  1. raw_clips/ 폴더에 촬영 클립 넣기"
echo "     (파일명 예: 01_인트로.mp4, 02_본론.mp4)"
echo "  2. bgm/ 폴더에 배경음악 넣기"
echo "  4. 프로젝트 루트 폴더에 '.env' 파일을 만들고 'GEMINI_API_KEY=내키값' 입력 (최초 1회 필수!)"
echo "  5. 터미널에서 'claude' 실행"
echo "  6. 'prompt.md를 참고해서 숏폼 영상 만들어줘' 입력"
echo ""
