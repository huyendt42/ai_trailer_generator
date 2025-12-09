import logging
import shutil
import json
from pathlib import Path

import cv2
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

from common import FRAMES_DIR, PROJECT_DIR, configs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)

logger.info("\nStarting scene-aware frame sampling\n")

def detect_scenes(video_path: str):
    logger.info(f"Detecting scenes in video: {video_path}")
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    
    # Threshold 27.0 là độ nhạy
    scene_manager.add_detector(ContentDetector(threshold=27.0))
    video_manager.set_downscale_factor()
    video_manager.start()
    
    scene_manager.detect_scenes(frame_source=video_manager)
    scene_list = scene_manager.get_scene_list()
    
    logger.info(f"Detected {len(scene_list)} scenes.\n")
    return scene_list

def save_scene_timestamps(scene_list):
    """Lưu thời gian Start/End (giây) của từng scene ra file JSON để make_clip.py dùng"""
    data = []
    for (start, end) in scene_list:
        data.append({
            "start": start.get_seconds(),
            "end": end.get_seconds()
        })
    
    json_path = PROJECT_DIR / "scenes.json"
    json_path.write_text(json.dumps(data, indent=2))
    logger.info(f"Saved timestamps to {json_path}")

def extract_keyframes(video_path: str, scene_list):
    """Vẫn trích xuất frame để dùng cho debug hoặc các thuật toán ranking khác nếu cần"""
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)

    for idx, (start, end) in enumerate(scene_list, start=1):
        scene_dir = FRAMES_DIR / f"scene_{idx}"
        scene_dir.mkdir(parents=True, exist_ok=True)
        
        start_frame = start.get_frames()
        end_frame = end.get_frames()
        mid_frame = (start_frame + end_frame) // 2

        # Dùng dict.fromkeys để tránh trùng index nếu scene quá ngắn
        keyframes = list(dict.fromkeys([
            start_frame + 3,  # Skip boundary blur
            mid_frame,        # Best scene representation
            end_frame - 3     # Avoid next scene transition
        ]))

        logger.info(f"Scene {idx}: extracting {len(keyframes)} keyframes.")

        for kf in keyframes:
            if kf < 0:
                continue
            cap.set(cv2.CAP_PROP_POS_FRAMES, kf)
            ret, frame = cap.read()
            if ret:
                out_path = scene_dir / f"frame_{kf}.jpg"
                cv2.imwrite(str(out_path), frame)

    cap.release()
    cv2.destroyAllWindows()

# --- MAIN ---
ROOT = Path(__file__).resolve().parents[1]
video_path = ROOT / "projects" / "LOL" / "video_input.mp4"

if not video_path.exists():
    # Fallback nếu chạy trực tiếp
    video_path = Path(configs["video_path"])

print(f"DEBUG: Đang xử lý video tại: {video_path}")

if not video_path.exists():
    logger.error(f"Không tìm thấy file video tại {video_path}")
else:
    scenes = detect_scenes(str(video_path))
    
    # [QUAN TRỌNG] Lưu timestamp để bước sau cắt video
    save_scene_timestamps(scenes)
    
    # Vẫn extract ảnh để có dữ liệu cho các bước khác
    extract_keyframes(str(video_path), scenes)
    logger.info("\nScene detection completed\n")