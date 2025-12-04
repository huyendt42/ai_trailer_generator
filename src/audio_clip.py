import os
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from common import CLIPS_DIR, VOICES_DIR, AUDIO_CLIPS_DIR, configs

AUDIO_CLIPS_DIR.mkdir(parents=True, exist_ok=True)

n_subplots = configs["subplot"]["n_subplots"]

clip_volume = configs["audio_clip"]["clip_volume"]
voice_volume = configs["audio_clip"]["voice_volume"]

for i in range(1, n_subplots + 1):

    scene_clip_dir = CLIPS_DIR / f"scene_{i}"
    scene_audio_dir = VOICES_DIR / f"scene_{i}"

    if not scene_clip_dir.exists() or not scene_audio_dir.exists():
        print(f"Scene {i}: Missing clip or audio folder, skip.")
        continue

    # lấy file video (clip)
    clip_files = [f for f in scene_clip_dir.glob("*.mp4")]
    if not clip_files:
        print(f"Scene {i}: No clip found, skip.")
        continue

    video_path = clip_files[0]

    # lấy audio
    audio_path = scene_audio_dir / "audio_1.wav"
    if not audio_path.exists():
        print(f"Scene {i}: No audio file found, skip.")
        continue

    video = VideoFileClip(str(video_path)).volumex(clip_volume)
    audio = AudioFileClip(str(audio_path)).volumex(voice_volume)

    final = video.set_audio(audio)

    out_dir = AUDIO_CLIPS_DIR / f"scene_{i}"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{video_path.stem}_with_audio.mp4"
    final.write_videofile(str(out_path), codec="libx264", audio_codec="aac")

    print(f"Scene {i}: Created audio clip → {out_path}")
