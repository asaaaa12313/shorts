"""Gemini API를 사용하여 영상 분석 → SRT 자막 생성"""
import os
import time
from google import genai
from app.core.config import GEMINI_API_KEY

PROMPT = """
당신은 트렌디한 인스타그램 릴스/유튜브 쇼츠 전문 영상 편집자입니다.
업로드된 영상을 분석하여 한글 자막(나레이션)을 작성해주세요.

[핵심 규칙]
- 자막은 반드시 5~6개를 만드세요. 영상 전체에 골고루 분배하세요.
- 각 자막은 10자 내외로 짧게 쓰세요. 절대 20자를 넘기지 마세요.
- AI 음성이 2초 안에 읽을 수 있는 길이여야 합니다.

[자막 예시]
1번: "여기 분위기 대박!" (후킹)
2번: "수제 디저트 맛집" (포인트)
3번: "이 비주얼 실화?" (감탄)
4번: "인테리어도 감성적" (포인트)
5번: "지금 바로 방문!" (CTA)

[자막 톤]
- 숏폼 트렌디한 톤. 딱딱하지 않게.
- 영상 화면에 보이는 것을 기반으로 작성.
- 배경음/무음이면 화면 묘사. 음성이 있으면 핵심만 요약.

[출력 형식]
- 표준 SRT 형식으로만 출력하세요. (번호, 타임코드, 텍스트)
- 타임코드: 2~3초 간격, 자막 사이 0.3초 빈 구간.
- SRT 외에 다른 텍스트 절대 금지.
"""


BUSINESS_TYPE_HINTS = {
    "카페": "이 영상은 카페/커피숍입니다. 음료, 디저트, 인테리어, 분위기 관련 감성적 자막을 만들어주세요.",
    "음식점": "이 영상은 음식점/맛집입니다. 음식의 맛, 비주얼, 식감을 강조하는 자막을 만들어주세요.",
    "골프": "이 영상은 골프 레슨/연습장입니다. 스윙, 자세, 레슨 관련 전문적이면서 역동적인 자막을 만들어주세요.",
    "태권도": "이 영상은 태권도장입니다. 운동, 성장, 교육 관련 활기찬 자막을 만들어주세요.",
    "뷰티": "이 영상은 뷰티/에스테틱/헤어샵입니다. 시술 과정, 변화, 케어 관련 세련된 자막을 만들어주세요.",
    "학원": "이 영상은 학원/교육기관입니다. 학습, 성장, 성과 관련 신뢰감 있는 자막을 만들어주세요.",
    "헬스": "이 영상은 헬스/PT/피트니스입니다. 운동, 체력, 변화 관련 동기부여 자막을 만들어주세요.",
    "병원": "이 영상은 병원/의원/클리닉입니다. 전문성, 신뢰, 케어 관련 격식있는 자막을 만들어주세요.",
    "기타": "",
}


def generate_subtitles(video_path: str, output_srt_path: str, api_key: str = "",
                       business_type: str = "") -> str:
    """영상을 Gemini API에 업로드하여 SRT 자막 생성"""
    key = api_key or GEMINI_API_KEY
    if not key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다")

    # 업종 힌트 추가
    prompt = PROMPT
    hint = BUSINESS_TYPE_HINTS.get(business_type, "")
    if hint:
        prompt = f"[업종 힌트] {hint}\n\n{PROMPT}"

    client = genai.Client(api_key=key)
    video_file = None

    try:
        video_file = client.files.upload(file=video_path)

        # 처리 완료 대기
        for _ in range(60):
            file_info = client.files.get(name=video_file.name)
            if file_info.state.name == "ACTIVE":
                break
            if file_info.state.name == "FAILED":
                raise RuntimeError("Gemini 서버에서 동영상 처리 실패")
            time.sleep(2)

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[video_file, prompt]
        )

        srt_content = response.text.strip()

        # 마크다운 백틱 제거
        if srt_content.startswith("```"):
            lines = srt_content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            srt_content = "\n".join(lines).strip()

        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        return srt_content

    finally:
        if video_file:
            try:
                client.files.delete(name=video_file.name)
            except Exception:
                pass


def _storytelling_timing(n_lines: int, duration: float) -> list[tuple[float, float]]:
    """후킹→설명→CTA 구조의 타이밍 분배 (문장 간 0.3초 호흡 포함)"""
    gap = 0.3  # 문장 간 호흡 시간
    if n_lines == 1:
        return [(0, duration)]
    if n_lines == 2:
        mid = duration * 0.4
        return [(0, mid - gap), (mid, duration - gap)]

    # 3줄 이상: 첫줄(후킹) 20% / 중간줄들(설명) 60% 균등 / 마지막줄(CTA) 20%
    hook_end = duration * 0.2
    cta_start = duration * 0.8
    mid_count = n_lines - 2
    mid_interval = (cta_start - hook_end) / mid_count

    timings = [(0, hook_end - gap)]
    for i in range(mid_count):
        s = hook_end + i * mid_interval
        e = s + mid_interval
        timings.append((s, e - gap))
    timings.append((cta_start, duration - gap))
    return timings


def generate_subtitles_from_text(user_text: str, output_srt_path: str, duration: float = 15.0) -> str:
    """사용자가 직접 입력한 텍스트를 SRT 형식으로 변환 (후킹→설명→CTA 타이밍)"""
    lines = [l.strip() for l in user_text.strip().split("\n") if l.strip()]
    if not lines:
        raise ValueError("자막 텍스트가 비어있습니다")

    timings = _storytelling_timing(len(lines), duration)
    srt_parts = []

    for i, (line, (start, end)) in enumerate(zip(lines, timings)):
        sh, sm, ss = int(start // 3600), int(start % 3600 // 60), start % 60
        eh, em, es = int(end // 3600), int(end % 3600 // 60), end % 60
        srt_parts.append(
            f"{i+1}\n"
            f"{sh:02d}:{sm:02d}:{ss:06.3f} --> {eh:02d}:{em:02d}:{es:06.3f}\n"
            f"{line}\n"
        )

    srt_content = "\n".join(srt_parts)
    with open(output_srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    return srt_content
