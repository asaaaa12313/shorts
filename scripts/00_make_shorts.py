import os
import glob
import subprocess
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip

def make_shorts():
    print("🎬 숏폼 영상 제작을 시작합니다!")
    
    # 1. 클립 로드
    raw_clips_dir = "raw_clips"
    clip_files = sorted(glob.glob(os.path.join(raw_clips_dir, "*.mp4")) + glob.glob(os.path.join(raw_clips_dir, "*.MP4")))
    
    if not clip_files:
        print("❌ 오류: raw_clips 폴더에 영상이 없습니다.")
        return
        
    print(f"✅ {len(clip_files)}개의 영상을 찾았습니다.")
    
    # 15초 길이를 위해 각 클립당 할당 시간 계산
    target_duration = 15.0
    clip_duration = target_duration / len(clip_files)
    
    processed_clips = []
    
    for idx, f in enumerate(clip_files):
        print(f"🔄 처리 중: {f} (목표 길이: {clip_duration:.2f}초)")
        try:
            vc = VideoFileClip(f)
            # 프레임을 1080x1920 비율에 맞춤 (가운데 크롭)
            vc = vc.resize(height=1920)
            
            # 중앙 크롭 (가로가 1080보다 크면 가운데 자름)
            w, h = vc.size
            if w > 1080:
                x_center = w / 2
                vc = vc.crop(x1=x_center - 540, y1=0, x2=x_center + 540, y2=1920)
            
            # 클립 길이 조절 (앞 1초 자르고 지정된 길이만큼 사용)
            start_time = min(1.0, vc.duration * 0.1)
            end_time = min(start_time + clip_duration, vc.duration)
            vc = vc.subclip(start_time, end_time)
            
            processed_clips.append(vc)
        except Exception as e:
            print(f"⚠️ {f} 처리 중 오류: {e}")
            
    if not processed_clips:
        print("❌ 오류: 처리 가능한 영상이 없습니다.")
        return
        
    # 조합
    print("🔄 영상을 하나로 합치는 중...")
    final_video = concatenate_videoclips(processed_clips, method="compose")
    
    # 배경음악 설정
    bgm_path = os.path.expanduser("~/Library/CloudStorage/GoogleDrive-tkfkdgowldms@gmail.com/내 드라이브/3.위즈더플래닝 디자인/숏폼/BGM/잔잔/Aves - Traffic Jams.mp3")
    if os.path.exists(bgm_path):
        print("🎵 잔잔한 BGM을 추가합니다...")
        bgm_clip = AudioFileClip(bgm_path).subclip(0, final_video.duration)
        # BGM 볼륨 20%로 낮춤 (원본 오디오가 있으면 유지)
        bgm_clip = bgm_clip.volumex(0.2)
        
        # 원본 영상 오디오와 믹스
        if final_video.audio is not None:
            new_audio = CompositeAudioClip([final_video.audio, bgm_clip])
        else:
            new_audio = bgm_clip
            
        final_video = final_video.set_audio(new_audio)
    else:
        print("⚠️ 설정된 BGM 파일이 없어서 영상 오디오만 사용합니다.")

    # 임시 출력
    temp_output = "temp/temp_video.mp4"
    print(f"🔄 임시 비디오 생성 중: {temp_output}")
    final_video.write_videofile(temp_output, fps=30, codec="libx264", audio_codec="aac", logger=None)
    
    # 생성된 비디오 메모리 해제
    for c in processed_clips:
        c.close()
    final_video.close()
    
    # 2. 자막 생성 (Gemini API 스크립트 호출)
    srt_output = "output/subs.srt"
    print(f"🤖 Gemini API를 활용하여 맥락 기반 자막을 생성합니다...")
    subprocess.run(["python3", "scripts/03_generate_subs.py", temp_output, srt_output], check=True)
    
    # 3. 자막 합성
    print(f"📝 생성된 자막({srt_output})을 원본 영상에 입히는 중...")
    final_output = "output/shorts/shortform_grove_banpo.mp4"
    
    # FFMPEG로 크고 임팩트 있는 자막 합성 (폰트 크기 대폭 상향: 15 -> 24 정도가 ffmpeg 에선 꽤 큼)
    # ffmpeg 자체 srt 자막 필터는 시스템 폰트를 사용
    # 프롬프트.md 요구사항(크기 1.5~2배 키움) 적용
    font_style = "FontName=NanumSquareB,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,MarginV=30,Alignment=2"
    
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", temp_output,
        "-vf", f"subtitles={srt_output}:force_style='{font_style}'",
        "-c:v", "libx264", "-c:a", "copy",
        final_output
    ]
    
    print(" ".join(ffmpeg_cmd))
    subprocess.run(ffmpeg_cmd, check=True)
    
    print(f"🎉 성공! 최종 숏폼 영상이 생성되었습니다: {final_output}")

if __name__ == "__main__":
    make_shorts()
