import logging
import json
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip

from common import (
    CLIPS_DIR,
    VOICES_DIR,
    PROJECT_DIR,
    SUBPLOTS_DIR,
    list_scenes,
    configs
)

# Lấy đường dẫn video gốc
ROOT = Path(__file__).resolve().parents[1]
VIDEO_PATH = ROOT / "projects" / "LOL" / "video_input.mp4"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_scene_timestamps():
    """Đọc file json do frame.py tạo ra"""
    json_path = PROJECT_DIR / "scenes.json"
    if not json_path.exists():
        return []
    return json.loads(json_path.read_text())

def main():
    logger.info("Starting REAL video clip creation (Distributed Mode)...")
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load danh sách subplot
    story_scenes = list_scenes(SUBPLOTS_DIR) 
    num_story_scenes = len(story_scenes)
    
    # 2. Load timestamp detect được từ frame.py
    video_timestamps = load_scene_timestamps()
    
    if not story_scenes:
        logger.error("No subplots found. Run subplot.py first.")
        return

    # Load Video gốc
    try:
        original_video = VideoFileClip(str(VIDEO_PATH))
        video_duration = original_video.duration
    except Exception as e:
        logger.error(f"Could not load input video at {VIDEO_PATH}: {e}")
        return

    # --- CHIẾN THUẬT: CHIA VÙNG (ZONING) ---
    # Chia video thành các khúc đều nhau để rải cảnh ra, tránh trùng lặp.
    # Ví dụ: Video dài 60s, có 6 cảnh truyện -> Mỗi cảnh được cấp quota 10s.
    zone_duration = video_duration / num_story_scenes if num_story_scenes > 0 else 10

    for i, scene_dir in enumerate(story_scenes):
        scene_name = scene_dir.name
        
        # --- AUDIO ---
        voice_path = VOICES_DIR / scene_name / "audio_1.wav"
        if not voice_path.exists():
            logger.warning(f"No voice for {scene_name}, skipping.")
            continue
            
        voice = AudioFileClip(str(voice_path))
        voice_dur = voice.duration
        
        # --- TÍNH TOÁN ĐIỂM BẮT ĐẦU (START TIME) ---
        # Xác định vùng thời gian cho cảnh này (Zone)
        zone_start_limit = i * zone_duration
        zone_end_limit = (i + 1) * zone_duration
        
        # 1. Cố gắng tìm một điểm cắt cảnh (scene cut) nằm trong vùng này
        candidates = []
        if video_timestamps:
            # Lọc ra các timestamp bắt đầu nằm trong zone
            candidates = [
                ts["start"] for ts in video_timestamps 
                if zone_start_limit <= ts["start"] < (zone_end_limit - 1) # Trừ hao 1s
            ]
        
        if candidates:
            # Nếu có điểm cắt đẹp trong vùng, lấy điểm đầu tiên
            start_t = candidates[0]
        else:
            # Nếu không có điểm cắt nào (hoặc detect lỗi), lấy luôn đầu vùng
            start_t = zone_start_limit

        # --- TÍNH ĐIỂM KẾT THÚC ---
        end_t = start_t + voice_dur
        
        # Kiểm tra biên: Nếu tràn ra ngoài video -> Dịch ngược lại
        if end_t > video_duration:
            end_t = video_duration
            start_t = max(0, end_t - voice_dur)
            
        # Kiểm tra chồng lấn: Nếu cảnh này lấn quá sâu sang vùng của cảnh sau?
        # Với trailer thì chấp nhận lấn một chút cũng được để ưu tiên đủ voice.

        try:
            # Cắt video
            final_clip = original_video.subclip(start_t, end_t)
            final_clip = final_clip.set_audio(None) 
            
            # Lưu file
            out_dir = CLIPS_DIR / scene_name
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "clip.mp4"
            
            final_clip.write_videofile(
                str(out_path),
                codec="libx264",
                audio_codec="aac",
                fps=24,
                logger=None
            )
            logger.info(f"{scene_name}: Zone [{zone_start_limit:.1f}s-{zone_end_limit:.1f}s] -> Picked {start_t:.1f}s")

        except Exception as e:
            logger.error(f"Error processing {scene_name}: {e}")

    original_video.close()
    logger.info("Distributed clip creation finished.")

if __name__ == "__main__":
    main()