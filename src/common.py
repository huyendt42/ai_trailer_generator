import yaml
import shutil
import logging
from pathlib import Path

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The folder containing common.py is 'src/', so we go up one level to get the Project Root
ROOT = Path(__file__).resolve().parents[1]

# Path to the main configuration file
CONFIGS_PATH = ROOT / "configs.yaml"

def parse_configs(configs_path: Path):
    """Load configuration from YAML file."""
    try:
        with open(configs_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Could not load configs.yaml: {e}. Using empty config.")
        return {}

# 1. Load base configurations (e.g., model IDs, parameters)
configs = parse_configs(CONFIGS_PATH)

# =========================================================
# CRITICAL: SYNC WITH UI (STREAMLIT)
# =========================================================

# The UI saves files to 'projects/LOL', so we force the backend to use this path.
PROJECT_DIR = ROOT / "projects" / "LOL"
VIDEO_PATH = PROJECT_DIR / "video_input.mp4"

# Override config values so other scripts (like frame.py) automatically use the new paths
configs["video_path"] = str(VIDEO_PATH)
configs["project_dir"] = "projects"
configs["project_name"] = "LOL"

# =========================================================

# 2. Define Output Directories
FRAMES_DIR = PROJECT_DIR / "frames"
FRAMES_RANKING_DIR = PROJECT_DIR / "frames_ranking"
SUBPLOTS_DIR = PROJECT_DIR / "subplots"
VOICES_DIR = PROJECT_DIR / "voices"
CLIPS_DIR = PROJECT_DIR / "clips"
AUDIO_CLIPS_DIR = PROJECT_DIR / "audio_clips"
TRAILER_DIR = PROJECT_DIR / "trailers"

# Update 'frames_dir' in configs for scripts like image_retrieval.py
configs["frames_dir"] = str(FRAMES_DIR)

def ensure_directories():
    """Ensure all necessary project directories exist."""
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

# Create directories immediately upon import
ensure_directories()

def clean_project_data():
    """
    CLEANUP FUNCTION:
    Deletes temporary data from previous runs (frames, voices, etc.)
    to ensure the new trailer is generated from the new video/plot.
    Keeps 'video_input.mp4', 'input_plot.txt', and the 'trailers' output folder.
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
        
        # Recreate the empty folder immediately
        folder.mkdir(parents=True, exist_ok=True)
    
    logger.info("--- CLEANUP COMPLETED ---\n")

def get_fps(video_path: Path):
    """Return the FPS of the video using MoviePy."""
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(str(video_path))
        fps = clip.fps
        clip.close()
        return fps
    except Exception as e:
        logger.error(f"Error loading FPS: {e}")
        return 24  # Default fallback

def list_scenes(folder: Path):
    """
    Return a sorted list of scene directories (e.g., scene_1, scene_2).
    """
    if not folder.exists():
        return []
    
    scenes = [d for d in folder.iterdir() if d.is_dir() and d.name.startswith("scene_")]
    
    # Sort numerically by the index in 'scene_X'
    try:
        return sorted(scenes, key=lambda x: int(x.name.split("_")[1]))
    except ValueError:
        return sorted(scenes)