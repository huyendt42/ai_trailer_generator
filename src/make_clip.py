import logging 
import re
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip

from common import (
    CLIPS_DIR,
    VOICES_DIR, 
    SUBPLOTS_DIR,
    FRAMES_RANKING_DIR,
    list_scenes,
    configs
)

# Lấy đường dẫn video gốc
ROOT = Path(__file__).resolve().parents[1]
VIDEO_PATH = ROOT / "projects" / "LOL" / "video_input.mp4"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_ranked_candidates(scene_name: str, fps: float):
    """
    Đọc danh sách các frame đã được AI chấm điểm từ folder frames_ranking.
    Trả về danh sách các ứng viên: [(score, timestamp_start, frame_idx), ...]
    Sắp xếp từ điểm cao xuống thấp.
    """
    ranking_dir = FRAMES_RANKING_DIR / scene_name
    if not ranking_dir.exists():
        return []
    
    files = list(ranking_dir.glob("*.jpg"))
    candidates = []

    for f in files:
        # Tên file dạng: 0.8521_frame_1500.jpg
        match = re.match(r"([\d\.]+)_frame_(\d+)\.jpg", f.name)
        if match:
            score = float(match.group(1))
            frame_idx = int(match.group(2))
            
            # Chuyển đổi frame index sang giây (Timestamp)
            timestamp = frame_idx / fps
            candidates.append((score, timestamp, frame_idx))
    
    # Sắp xếp giảm dần theo điểm số (Score cao nhất lên đầu)
    return sorted(candidates, key=lambda x: x[0], reverse=True)

def is_overlapping(start, duration, used_segments, buffer=2.0):
    """
    Kiểm tra xem đoạn video dự kiến (start -> start + duration)
    có bị trùng với các đoạn đã dùng trước đó không.
    buffer: Khoảng cách an toàn (giây) để tránh lặp mép.
    """
    end = start + duration
    for u_start, u_end in used_segments:
        # Công thức kiểm tra giao nhau của 2 khoảng thời gian
        # Nếu (Start A < End B) và (End A > Start B) thì là trùng nhau
        if (start < u_end - buffer) and (end > u_start + buffer):
            return True
    return False

def main():
    logger.info("Starting SMART video clip creation (Anti-Overlap Mode)...")
    
    # Tạo thư mục chứa clip đầu ra
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    story_scenes = list_scenes(SUBPLOTS_DIR) 
    num_story_scenes = len(story_scenes)
    
    # --- DANH SÁCH CÁC ĐOẠN ĐÃ DÙNG ---
    # Đây là bí quyết chống lặp: lưu lại start/end của các cảnh trước
    used_segments = []
    used_frame_indices = set()

    # Load Video gốc
    try:
        original_video = VideoFileClip(str(VIDEO_PATH))
        video_duration = original_video.duration
        video_fps = original_video.fps
    except Exception as e:
        logger.error(f"Could not load input video at {VIDEO_PATH}: {e}")
        return

    # Fallback zoning (Chia vùng dự phòng nếu AI không tìm được ảnh)
    zone_duration = video_duration / num_story_scenes if num_story_scenes > 0 else 10

    for i, scene_dir in enumerate(story_scenes):
        scene_name = scene_dir.name # ví dụ: scene_1
        
        # --- 1. LẤY AUDIO VOICE ---
        voice_path = VOICES_DIR / scene_name / "audio_1.wav"
        if not voice_path.exists():
            logger.warning(f"No voice for {scene_name}, skipping.")
            continue
            
        voice = AudioFileClip(str(voice_path))
        voice_dur = voice.duration
        
        # --- 2. CHIẾN THUẬT CHỌN ĐIỂM BẮT ĐẦU (CHỐNG TRÙNG) ---
        start_t = None
        
        # Lấy danh sách ứng viên từ AI (đã sort từ xịn nhất -> kém nhất)
        candidates = get_ranked_candidates(scene_name, video_fps)
        
        
        found_candidate = False
        for score, ts, frame_idx in candidates:
        # 1) Nếu frame này đã được dùng cho subplot trước -> bỏ qua
            if frame_idx in used_frame_indices:
                logger.info(
                    f"[{scene_name}] Skip frame {frame_idx} (already used in previous scene)"
                )
                continue
        # 2) Nếu không overlap về thời gian với các đoạn trước -> chọn
            if not is_overlapping(ts, voice_dur, used_segments):
                start_t = ts
                used_frame_indices.add(frame_idx)
                logger.info(f"[{scene_name}] AI Selected: frame {frame_idx} | Score {score:.4f} at {ts:.2f}s (Unique)")
                found_candidate = True
                break
        
        if not found_candidate:
            # Nếu tất cả ứng viên AI đều bị trùng (hoặc không có ứng viên)
            # -> Dùng chiến thuật Fallback Zoning: Tìm một vùng trống
            logger.warning(f"[{scene_name}] All AI frames overlapped or none found. Finding empty zone...")
            
            zone_start = i * zone_duration
            
            # Thử tìm điểm trống bằng cách dò (Brute force search đơn giản)
            fallback_t = zone_start
            retries = 0
            while is_overlapping(fallback_t, voice_dur, used_segments) and retries < 20:
                fallback_t += 5.0 # Dịch đi 5s mỗi lần để tìm đất trống
                if fallback_t > video_duration - voice_dur: 
                    fallback_t = 0 # Quay vòng về đầu nếu hết video
                retries += 1
            
            start_t = fallback_t
            logger.warning(f"-> Fallback used at {start_t:.2f}s")

        # --- 3. TÍNH TOÁN ĐIỂM KẾT THÚC ---
        end_t = start_t + voice_dur
        
        # Xử lý tràn video (nếu đoạn cắt vượt quá độ dài video gốc)
        if end_t > video_duration:
            end_t = video_duration
            start_t = max(0, end_t - voice_dur)

        # --- 4. CẬP NHẬT DANH SÁCH ĐÃ DÙNG ---
        used_segments.append((start_t, end_t))

        # --- 5. CẮT VÀ XUẤT FILE ---
        try:
            # Cắt đoạn video
            final_clip = original_video.subclip(start_t, end_t)
            
            # Tắt tiếng video gốc (để audio_clip.py lo phần tiếng sau)
            final_clip = final_clip.set_audio(None) 
            
            # Tạo folder scene đầu ra
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
            logger.info(f"--> Saved {scene_name}: {start_t:.1f}s to {end_t:.1f}s")

        except Exception as e:
            logger.error(f"Error processing {scene_name}: {e}")

    original_video.close()
    logger.info("Smart Clip Creation (Anti-Overlap) finished.")

if __name__ == "__main__":
    main()