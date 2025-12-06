import logging
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip

from common import CLIPS_DIR, VOICES_DIR, AUDIO_CLIPS_DIR, configs, list_scenes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting audio mixing...")
    AUDIO_CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    # Lấy volume từ config (mặc định 1.0 nếu thiếu)
    audio_cfg = configs.get("audio_clip", {})
    clip_vol = float(audio_cfg.get("clip_volume", 0.0)) # Mặc định tắt tiếng video gốc (nếu là ảnh thì ko có tiếng)
    voice_vol = float(audio_cfg.get("voice_volume", 1.5)) # Tăng voice lên chút cho to

    # Lấy danh sách scene từ folder CLIPS_DIR
    scenes = list_scenes(CLIPS_DIR)
    
    if not scenes:
        logger.error(f"No clips found in {CLIPS_DIR}. Did make_clip.py run correctly?")
        return

    for scene_dir in scenes:
        scene_name = scene_dir.name # scene_1
        
        # 1. Tìm video clip
        # make_clip.py lưu file là "clip.mp4"
        video_path = scene_dir / "clip.mp4"
        if not video_path.exists():
            # Fallback: tìm bất kỳ file mp4 nào
            mp4s = list(scene_dir.glob("*.mp4"))
            if mp4s:
                video_path = mp4s[0]
            else:
                logger.warning(f"{scene_name}: No mp4 found, skipping.")
                continue

        # 2. Tìm audio voice
        # voice.py lưu tại voices/scene_1/audio_1.wav
        audio_path = VOICES_DIR / scene_name / "audio_1.wav"
        if not audio_path.exists():
            logger.warning(f"{scene_name}: No voice audio found, skipping.")
            continue

        # 3. Trộn (Mix)
        try:
            video = VideoFileClip(str(video_path))
            voice = AudioFileClip(str(audio_path))

            # Điều chỉnh âm lượng
            if video.audio:
                video = video.volumex(clip_vol)
            
            # Gán voice mới vào (giữ độ dài theo video)
            final_audio = voice.volumex(voice_vol)
            final_clip = video.set_audio(final_audio)

            # 4. Xuất file
            out_dir = AUDIO_CLIPS_DIR / scene_name
            out_dir.mkdir(parents=True, exist_ok=True)
            
            out_path = out_dir / "final.mp4"
            
            final_clip.write_videofile(
                str(out_path),
                codec="libx264",
                audio_codec="aac",
                logger=None
            )
            logger.info(f"Mixed audio for {scene_name} -> {out_path}")
            
            # Close clips to free memory
            video.close()
            voice.close()

        except Exception as e:
            logger.error(f"Failed to mix {scene_name}: {e}")

    logger.info("Audio mixing finished.")

if __name__ == "__main__":
    main()