from pathlib import Path
# Thêm AudioFileClip, CompositeAudioClip, afx để xử lý nhạc
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip, afx
from common import AUDIO_CLIPS_DIR, TRAILER_DIR, configs

# --- CẤU HÌNH ---
# Số subplot (scene)
n_subplots = configs["subplot"]["n_subplots"]
# Định nghĩa đường dẫn file nhạc (nằm cùng cấp với các folder output trong project)
MUSIC_PATH = AUDIO_CLIPS_DIR.parent / "background_music.wav"

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

# --- THÊM NHẠC NỀN & LOOP ---
if MUSIC_PATH.exists():
    print(f"Found background music: {MUSIC_PATH.name}")
    try:
        bg_music = AudioFileClip(str(MUSIC_PATH))
        bg_music = afx.audio_loop(bg_music, duration=final.duration)
        bg_music = bg_music.volumex(0.5)
        original_audio = final.audio
        final_mixed_audio = CompositeAudioClip([original_audio, bg_music])
        final = final.set_audio(final_mixed_audio)
        print("Background music added and looped successfully.")
        
    except Exception as e:
        print(f"Error adding background music: {e}")
else:
    print("No background music found. Skipping.")

# --- XUẤT FILE ---
output = TRAILER_DIR / "trailer_1.mp4"
final.write_videofile(str(output), codec="libx264", audio_codec="aac")

print(f"Trailer created → {output}")
