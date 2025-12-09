import yaml
import shutil
import logging
from pathlib import Path

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lấy đường dẫn gốc của Project (Thư mục cha của src/)
ROOT = Path(__file__).resolve().parents[1]

# Đường dẫn file cấu hình
CONFIGS_PATH = ROOT / "configs.yaml"

def parse_configs(configs_path: Path):
    """Load configuration from YAML file."""
    try:
        with open(configs_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Could not load configs.yaml: {e}. Using empty config.")
        return {}

# 1. Load các cấu hình cơ bản
configs = parse_configs(CONFIGS_PATH)

# =========================================================
# CẤU HÌNH ĐƯỜNG DẪN (ĐỒNG BỘ VỚI UI)
# =========================================================

# UI lưu file vào 'projects/LOL', backend bắt buộc dùng đúng đường dẫn này.
PROJECT_DIR = ROOT / "projects" / "LOL"
VIDEO_PATH = PROJECT_DIR / "video_input.mp4"

# Cập nhật ngược lại vào configs để các file khác dùng chung
configs["video_path"] = str(VIDEO_PATH)
configs["project_dir"] = "projects"
configs["project_name"] = "LOL"

# =========================================================

# 2. Định nghĩa các thư mục đầu ra (Output Directories)
FRAMES_DIR = PROJECT_DIR / "frames"
FRAMES_RANKING_DIR = PROJECT_DIR / "frames_ranking"
SUBPLOTS_DIR = PROJECT_DIR / "subplots"
VOICES_DIR = PROJECT_DIR / "voices"
CLIPS_DIR = PROJECT_DIR / "clips"
AUDIO_CLIPS_DIR = PROJECT_DIR / "audio_clips"
TRAILER_DIR = PROJECT_DIR / "trailers"

# Cập nhật frames_dir vào config cho image_retrieval.py
configs["frames_dir"] = str(FRAMES_DIR)

def ensure_directories():
    """Tạo tất cả các thư mục cần thiết nếu chưa có."""
    dirs = [
        PROJECT_DIR,
        FRAMES_DIR,
        FRAMES_RANKING_DIR,
        SUBPLOTS_DIR,
        VOICES_DIR,
        CLIPS_DIR,
        AUDIO_CLIPS_DIR,
        TRAILER_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Tạo thư mục ngay khi import file này
ensure_directories()

def clean_project_data():
    """
    Hàm dọn dẹp dữ liệu cũ trước khi chạy mới.
    Giữ lại video gốc và plot đầu vào.
    """
    logger.info("--- CLEANING UP OLD PROJECT DATA ---")
    
    targets = [
        FRAMES_DIR,
        FRAMES_RANKING_DIR,
        SUBPLOTS_DIR,
        VOICES_DIR,
        CLIPS_DIR,
        AUDIO_CLIPS_DIR
    ]

    for folder in targets:
        if folder.exists():
            try:
                shutil.rmtree(folder)
                logger.info(f"Deleted: {folder.name}")
            except Exception as e:
                logger.error(f"Error deleting {folder.name}: {e}")
        
        # Tạo lại thư mục rỗng ngay lập tức
        folder.mkdir(parents=True, exist_ok=True)
    
    logger.info("--- CLEANUP COMPLETED ---\n")

def get_fps(video_path: Path):
    """Lấy FPS của video dùng MoviePy."""
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(str(video_path))
        fps = clip.fps
        clip.close()
        return fps
    except Exception as e:
        logger.error(f"Error loading FPS: {e}")
        return 24  # Fallback mặc định

def list_scenes(folder: Path):
    """
    Trả về danh sách các thư mục scene (ví dụ: scene_1, scene_2) đã được sắp xếp.
    """
    if not folder.exists():
        return []
    
    scenes = [d for d in folder.iterdir() if d.is_dir() and d.name.startswith("scene_")]
    
    # Sắp xếp theo số thứ tự trong tên scene (scene_1, scene_2, ...)
    try:
        return sorted(scenes, key=lambda x: int(x.name.split("_")[1]))
    except ValueError:
        return sorted(scenes)