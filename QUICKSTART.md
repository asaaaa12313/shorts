# 🎬 숏폼 자동 생성 - 빠른 시작 가이드

## 지금 바로 따라하기

### STEP 1: 프로젝트 폴더 만들기
원하는 위치에 폴더를 만들고 이 파일들을 넣으세요.
```bash
# 예: 바탕화면에 만들기
cd ~/Desktop
mkdir shortform_project
cd shortform_project
```

### STEP 2: 세팅 파일 복사
다운로드 받은 `prompt.md`와 `setup.sh`를 이 폴더에 넣으세요.

### STEP 3: 초기 세팅 실행
```bash
bash setup.sh
```
이 스크립트가 자동으로:
- ✅ 필요한 폴더 구조 생성
- ✅ FFmpeg 설치 여부 확인
- ✅ Python 패키지 설치 (Whisper, MoviePy 등)
- ✅ 한글 폰트 다운로드

### STEP 4: FFmpeg 설치 (아직 안 된 경우)
```bash
brew install ffmpeg
```

### STEP 5: 소재 넣기
```
raw_clips/ 폴더에 → 촬영 클립 넣기 (01_인트로.mp4, 02_본론.mp4 ...)
bgm/ 폴더에       → 배경음악 파일 넣기 (MP3 또는 WAV)
```

### STEP 6: 클로드 코드 실행
```bash
claude
```

### STEP 7: 명령어 입력
```
prompt.md를 참고해서 raw_clips 폴더의 영상들로 15초 숏폼을 만들어줘.
자막은 하단 중앙 흰색 글씨에 검정 테두리, bgm 폴더의 음악을 배경으로 깔아줘.
```

### STEP 8: 결과 확인
`output/` 폴더에 플랫폼별 영상이 생성됩니다:
- `output/reels/` → 인스타그램
- `output/shorts/` → 유튜브
- `output/tiktok/` → 틱톡

---

## 수정이 필요할 때

클로드 코드에 자연어로 바로 말하면 됩니다:

| 상황 | 명령 예시 |
|------|-----------|
| 자막이 작을 때 | "자막 크기를 22로 키워줘" |
| 음악이 시끄러울 때 | "BGM 볼륨 15%로 낮춰줘" |
| 특정 클립 제거 | "02번 클립 빼고 다시 만들어줘" |
| 순서 변경 | "03 → 01 → 02 순서로 바꿔줘" |
| 자막 위치 변경 | "자막을 화면 중앙으로 올려줘" |
| 전환 효과 변경 | "전환을 페이드 말고 컷으로 해줘" |

---

## 문제 해결

| 증상 | 해결 방법 |
|------|-----------|
| `ffmpeg: command not found` | `brew install ffmpeg` 실행 |
| `brew: command not found` | Homebrew 먼저 설치: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` |
| 자막이 깨짐 (□□□) | fonts/ 폴더에 한글 .ttf 폰트 파일 넣기 |
| Whisper 느림 | 모델을 `base`로 변경 (정확도↓ 속도↑) |
| 영상이 가로로 나옴 | prompt.md에서 이미 9:16 자동 변환 설정됨, 그래도 문제면 "세로로 다시 만들어줘" |
