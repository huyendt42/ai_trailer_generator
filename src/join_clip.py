from pathlib import Path
from moviepy.editor import VideoFileClip, concatenate_videoclips
from common import AUDIO_CLIPS_DIR, TRAILER_DIR, configs

# Số subplot (scene)
n_subplots = configs["subplot"]["n_subplots"]

TRAILER_DIR.mkdir(parents=True, exist_ok=True)

clips = []

print("Collecting scene clips...")

for i in range(1, n_subplots + 1):
    scene_dir = AUDIO_CLIPS_DIR / f"scene_{i}"

    if not scene_dir.exists():
        print(f"Scene {i}: audio clip folder missing → skip")
        continue

    scene_clips = sorted(scene_dir.glob("*.mp4"))

    if not scene_clips:
        print(f"Scene {i}: no audio clip found → skip")
        continue

    video_path = scene_clips[0]
    print(f"Scene {i}: Using {video_path}")

    clip = VideoFileClip(str(video_path))
    clips.append(clip)

if not clips:
    raise RuntimeError("No clips found to join. Check audio_clip.py output.")

print(f"Joining {len(clips)} scene clips...")
final = concatenate_videoclips(clips, method="compose")

output = TRAILER_DIR / "trailer_1.mp4"
final.write_videofile(str(output), codec="libx264", audio_codec="aac")

print(f"Trailer created → {output}")
