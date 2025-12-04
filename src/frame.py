import logging
import shutil
from pathlib import Path

import cv2
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

from common import FRAMES_DIR, configs


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)

logger.info("\nStarting scene-aware frame sampling\n")


def detect_scenes(video_path: str):
    """
    Detect scene boundaries in a video using PySceneDetect.

    This function analyzes the visual content of the video to detect
    significant changes in pixel distribution (e.g., scene transitions,
    hard cuts, fade transitions). It returns a list of scene boundary
    tuples (start_time, end_time).

    Args:
        video_path (str):
            Path to the input video file.

    Returns:
        list[(Timecode, Timecode)]:
            A list of scene boundaries.
            Each element contains:
            - start_time: beginning frame/time of the scene
            - end_time: ending frame/time of the scene

    """
    logger.info(f"Detecting scenes in video: {video_path}")

    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()

    scene_manager.add_detector(ContentDetector(threshold=27.0))

    video_manager.set_downscale_factor()

    video_manager.start()

    scene_manager.detect_scenes(frame_source=video_manager)
    scene_list = scene_manager.get_scene_list()

    logger.info(f"Detected {len(scene_list)} scenes.\n")
    return scene_list


def extract_keyframes(video_path: str, scene_list):
    """
    Extract representative keyframes from each detected scene.

    Keyframes chosen:
        - Start keyframe: (start_frame + 3)
            Skips 2 frames after the cut to avoid blur or fade artifacts.
        - Mid keyframe: midpoint between start_frame & end_frame
            Often contains the clearest depiction of the scene’s content.
        - End keyframe: (end_frame - 3)
            Avoids frames belonging to the upcoming scene transition.

    Args:
        video_path (str):
            Path to the video used for frame extraction.

        scene_list (list[(Timecode, Timecode)]):
            List of detected scenes returned by `detect_scenes()`.
            Each element contains start and end boundaries of a scene.

    Returns:
        None – Saves extracted keyframes as JPG files under:
            FRAMES_DIR/scene_x/frame_<index>.jpg
    """
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

        keyframes = list(dict.fromkeys([
            start_frame + 3,  # Skip boundary blur
            mid_frame,        # Best scene representation
            end_frame - 3     # Avoid next scene transition
        ]))

        logger.info(f"Scene {idx}: extracting {len(keyframes)} keyframes.")

        for kf in keyframes:
            cap.set(cv2.CAP_PROP_POS_FRAMES, kf)
            ret, frame = cap.read()
            if ret:
                out_path = scene_dir / f"frame_{kf}.jpg"
                cv2.imwrite(str(out_path), frame)

    cap.release()
    cv2.destroyAllWindows()


video_path = configs["video_path"]

scenes = detect_scenes(video_path)

extract_keyframes(video_path, scenes)

logger.info("\nScene-aware frame sampling completed\n")
