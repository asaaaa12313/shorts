import os
import sys
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

def generate_context_aware_subtitles(video_path, output_srt_path):
    print(f"\n[Step 3] Gemini API 기반 자동 자막(나레이션) 생성 시작...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ 오류: GEMINI_API_KEY가 설정되지 않았습니다.")
        print("   프로젝트 루트 폴더에 .env 파일을 만들고 GEMINI_API_KEY=당신의_키 를 입력해주세요.")
        sys.exit(1)

    print(f"🎬 동영상 파일 업로드 준비 중: {os.path.basename(video_path)}")
    
    client = genai.Client(api_key=api_key)
    video_file = None
    try:
        # 1. 파일 업로드
        print("⏳ Gemini 서버로 동영상 업로드 중... (용량에 따라 수 분 소요될 수 있습니다)")
        video_file = client.files.upload(file=video_path)
        
        # 2. 파일 처리 완료 대기 (동영상은 서버에서 처리 시간이 필요함)
        print("⏳ 동영상 처리 대기 중...")
        while True:
            file_info = client.files.get(name=video_file.name)
            if file_info.state.name == "ACTIVE":
                print("✅ 동영상 처리 완료!")
                break
            elif file_info.state.name == "FAILED":
                print("❌ 동영상 처리 실패. Gemini 서버 오류입니다.")
                sys.exit(1)
            time.sleep(2)
            
        # 3. 프롬프트 작성 및 컨텐츠 분석 요청
        print("🤖 영상 분석 및 자막 텍스트(SRT) 생성 중...")
        
        prompt = """
        당신은 트렌디한 인스타그램 릴스/유튜브 쇼츠 전문 영상 편집자입니다.
        업로드된 영상의 '화면 내용(비전)'과 '소리(오디오)'를 모두 분석하여 완성도 높은 한글 자막(나레이션)을 작성해주세요.

        [자막 작성 원칙]
        1. 단순한 대화가 아닌, 영상의 내용/상황/감정/분위기를 설명하는 임팩트 있는 '나레이션형 자막'을 생성하세요.
           (예: "지글지글 맛있게 익어가는 고기!", "헉, 골프장 뷰 대박 ⛳", "오늘 하루도 완벽하게 마무리 ✨")
        2. 영상에서 아무 목적어 없이 단순 배경음(바람소리, 고기 굽는 소리 등)만 나거나 아예 무음인 경우, 엉뚱한 대화(할루시네이션)를 절대 만들지 마세요. 오직 '화면에서 보이는 상황'을 재미있는 자막으로 묘사하세요.
        3. 만약 명확하고 의미 있는 한국어 음성(사람의 말)이 있다면, 그 내용을 살리되 숏폼에 맞게 핵심만 요약해서 띄워주세요.
        4. 영상 기획(음식, 스포츠, 브이로그 등)의 맥락을 완벽히 이해하고 그에 맞는 전문 용어나 톤앤매너를 사용하세요.

        [출력 구조]
        - 반드시 표준 SRT 파일 형식으로만 출력하세요. (번호, 타임코드, 텍스트)
        - 타임코드는 릴스/쇼츠 호흡에 맞게 1.5초~2.5초 간격으로 짧고 빠르게 넘어가도록 설정하세요.
        - 영상 전체 길이(15초 내외)에 맞게 자막을 분배하세요.
        - SRT 형식 규격 외에 다른 어떤 부연 설명이나 마크다운 태그(```srt 등)도 포함하지 마세요.
        """
        
        # 최신 모델 사용 (1.5 Flash가 속도/가성비/멀티모달 처리에 적합)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[
                video_file, 
                prompt
            ]
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
            
        with open(output_srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
            
        print(f"🎉 성공: 자막 생성 완료 ({output_srt_path})")
        
    except Exception as e:
        print(f"❌ 자막 생성 중 오류 발생: {e}")
        sys.exit(1)
    finally:
        # 4. 파일 정리 (서버에서 삭제)
        if video_file:
            try:
                client.files.delete(name=video_file.name)
                print("🧹 서버 임시 파일 정리 완료.")
            except Exception as e:
                pass

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("사용법: python 03_generate_subs.py <입력동영상경로> <출력SRT경로>")
        sys.exit(1)
        
    input_video = sys.argv[1]
    output_srt = sys.argv[2]
    
    if not os.path.exists(input_video):
        print(f"❌ 오류: 입력 파일을 찾을 수 없습니다: {input_video}")
        sys.exit(1)
        
    generate_context_aware_subtitles(input_video, output_srt)
