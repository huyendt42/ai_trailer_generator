import yaml
from pathlib import Path

# Folder chứa file common.py là: src/common.py → ta đi lên 1 cấp để tới thư mục gốc project
ROOT = Path(__file__).resolve().parents[1]

# Đường dẫn file config
CONFIGS_PATH = ROOT / "configs.yaml"

def parse_configs(configs_path: Path):
    with open(configs_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


configs = parse_configs(CONFIGS_PATH)

PROJECT_DIR = ROOT / configs["project_dir"] / configs["project_name"]

VIDEO_PATH = ROOT / configs["video_path"]  # video gốc

FRAMES_DIR = PROJECT_DIR / "frames"
FRAMES_RANKING_DIR = PROJECT_DIR / "frames_ranking"
SUBPLOTS_DIR = PROJECT_DIR / "subplots"
VOICES_DIR = PROJECT_DIR / "voices"
CLIPS_DIR = PROJECT_DIR / "clips"
AUDIO_CLIPS_DIR = PROJECT_DIR / "audio_clips"
TRAILER_DIR = PROJECT_DIR / "trailers"

def ensure_directories():
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


# Tự động đảm bảo các folder tồn tại
ensure_directories()


def get_fps(video_path: Path):
    """Trả về FPS của video bằng MoviePy"""
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(str(video_path))
        return clip.fps
    except Exception as e:
        print("Error loading FPS:", e)
        return None


def list_scenes(folder: Path):
    """Danh sách thư mục scene_x theo thứ tự tăng dần"""
    return sorted([d for d in folder.iterdir() if d.is_dir() and d.name.startswith("scene_")],
                  key=lambda x: int(x.name.split("_")[1]))


def debug_print_paths():
    print("\n=== PATH DEBUG ===")
    print("ROOT:", ROOT)
    print("PROJECT_DIR:", PROJECT_DIR)
    print("VIDEO_PATH:", VIDEO_PATH)
    print("FRAMES_DIR:", FRAMES_DIR)
    print("FRAMES_RANKING_DIR:", FRAMES_RANKING_DIR)
    print("SUBPLOTS_DIR:", SUBPLOTS_DIR)
    print("VOICES_DIR:", VOICES_DIR)
    print("CLIPS_DIR:", CLIPS_DIR)
    print("AUDIO_CLIPS_DIR:", AUDIO_CLIPS_DIR)
    print("TRAILER_DIR:", TRAILER_DIR)
    print("==================\n")
