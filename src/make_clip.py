import logging
import math
from pathlib import Path

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
)

from common import (
    FRAMES_DIR,
    VOICES_DIR,
    CLIPS_DIR,
    SUBPLOTS_DIR,
    configs,
    list_scenes,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


def get_scene_dirs():
    # Ưu tiên lấy theo subplots (scene_1, scene_2, ...)
    scenes = list_scenes(SUBPLOTS_DIR)
    if not scenes:
        scenes = list_scenes(FRAMES_DIR)
    if not scenes:
        raise RuntimeError(f"No scene directories found in {SUBPLOTS_DIR} or {FRAMES_DIR}")
    return scenes


def get_frames_for_scene(scene_dir: Path, max_frames_per_scene: int = 12):
    # Tìm ảnh trong thư mục frames/scene_x
    img_dir = FRAMES_DIR / scene_dir.name
    if not img_dir.exists():
        logger.warning("No frame directory for %s at %s", scene_dir.name, img_dir)
        return []

    imgs = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        imgs.extend(sorted(img_dir.glob(ext)))

    if not imgs:
        logger.warning("No frame images found in %s", img_dir)
        return []

    if len(imgs) > max_frames_per_scene:
        step = max(1, len(imgs) // max_frames_per_scene)
        imgs = imgs[::step][:max_frames_per_scene]

    return imgs


def build_scene_clip(scene_dir: Path, output_fps: int = 24):
    scene_name = scene_dir.name
    voice_path = VOICES_DIR / scene_name / "audio_1.wav"

    if not voice_path.exists():
        logger.warning("Missing voice for %s at %s, skipping.", scene_name, voice_path)
        return None

    audio = AudioFileClip(str(voice_path))
    total_duration = float(audio.duration)

    clip_cfg = configs.get("clip", {})
    max_frames_per_scene = int(clip_cfg.get("max_frames_per_scene", 12))
    min_frame_duration = float(clip_cfg.get("min_frame_duration", 0.15))

    frames = get_frames_for_scene(scene_dir, max_frames_per_scene=max_frames_per_scene)

    if not frames:
        # Nếu không có frame thì tạo màn hình đen + audio
        logger.warning("No frames for %s, using black screen.", scene_name)
        from moviepy.editor import ColorClip

        w, h = 1280, 720
        video = ColorClip(size=(w, h), color=(0, 0, 0), duration=total_duration)
        return video.set_audio(audio)

    n_frames = len(frames)
    per_frame_duration = max(total_duration / n_frames, min_frame_duration)

    img_clips = [
        ImageClip(str(p)).set_duration(per_frame_duration)
        for p in frames
    ]

    video = concatenate_videoclips(img_clips, method="compose")
    # Ép duration khớp audio (cắt hoặc kéo nhẹ)
    video = video.set_duration(total_duration).set_audio(audio)

    logger.info("Built clip for %s with %d frames, duration ~%.2fs",
                scene_name, n_frames, total_duration)
    return video


def assemble_scene_clips():
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    clip_cfg = configs.get("clip", {})
    output_fps = int(clip_cfg.get("output_fps", 24))

    scenes = get_scene_dirs()
    logger.info("Found %d scenes: %s", len(scenes), [s.name for s in scenes])

    scene_video_paths = []

    for scene_dir in scenes:
        clip = build_scene_clip(scene_dir, output_fps=output_fps)
        if clip is None:
            continue

        out_path = CLIPS_DIR / f"{scene_dir.name}.mp4"
        logger.info("Writing clip for %s to %s", scene_dir.name, out_path)
        clip.write_videofile(
            str(out_path),
            fps=output_fps,
            codec="libx264",
            audio_codec="aac",
        )
        scene_video_paths.append(out_path)

    if not scene_video_paths:
        raise RuntimeError("No scene clips were created. Check frames and voices folders.")

    logger.info("Created %d scene clips in %s", len(scene_video_paths), CLIPS_DIR)
    return scene_video_paths


def main():
    logger.info("Starting clip assembly (per-scene)...")
    assemble_scene_clips()
    logger.info("Clip assembly finished.")


if __name__ == "__main__":
    main()
