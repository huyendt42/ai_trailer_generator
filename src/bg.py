import os
import json
from pathlib import Path

import google.generativeai as genai
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeAudioClip,
    TextClip,
    ColorClip,
    CompositeVideoClip,
    concatenate_videoclips,
)

from TTS.api import TTS
from common import (
    ROOT,
    PROJECT_DIR,
    SUBPLOTS_DIR,
    VOICES_DIR,
    TRAILER_DIR,
    configs,
)

N_SUBPLOTS = configs["subplot"]["n_subplots"]
INTRO_DIR = PROJECT_DIR / "intro"
OUTRO_DIR = PROJECT_DIR / "outro"
ASSETS_MUSIC_DIR = ROOT / "assets" / "music"

MAIN_TRAILER_PATH = TRAILER_DIR / "trailer_1.mp4"
FINAL_TRAILER_PATH = TRAILER_DIR / "trailer_ai_final.mp4"

INTRO_DIR.mkdir(parents=True, exist_ok=True)
OUTRO_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_MUSIC_DIR.mkdir(parents=True, exist_ok=True)


def load_all_subplots():
    texts = []
    for i in range(1, N_SUBPLOTS + 1):
        p = SUBPLOTS_DIR / f"scene_{i}" / "subplot.txt"
        if p.exists():
            texts.append(p.read_text().strip())
    return "\n\n".join(texts)


def configure_gemini():
    if "GEMINI_API_KEY" not in os.environ:
        raise RuntimeError(
            "Bạn chưa đặt biến môi trường GEMINI_API_KEY.\n"
            "Hãy chạy:\n\nexport GEMINI_API_KEY=\"YOUR_API_KEY\"\n"
        )
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])


def call_gemini_for_intro_outro(plot_text: str) -> dict:
    configure_gemini()

    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
You are an expert cinematic trailer narrator.
Read this game plot and produce:

1. "tone": Emotional tone (few words)
2. "intro_text": 7–12 sec spoken intro
3. "outro_text": 5–9 sec spoken outro
4. "music_style": type of music fitting the trailer

Return ONLY JSON.

Plot:
\"\"\"
{plot_text}
\"\"\"
"""

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.9, "max_output_tokens": 500},
    )

    text = response.text.strip()

    try:
        return json.loads(text)
    except:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise RuntimeError(f"Gemini trả về JSON sai:\n{text}")
        return json.loads(text[start:end+1])


def get_tts():
    tts = TTS(model_id=configs["voice"]["model_id"]).to(configs["voice"]["device"])
    return tts


def tts_to_file(tts, text, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    tts.tts_to_file(text=text, file_path=str(out))


def create_text_video(text, audio_path, out_path, style="dark"):
    audio = AudioFileClip(str(audio_path))
    dur = audio.duration

    if style == "light":
        bg_color = (240, 240, 240)
        text_color = "black"
    else:
        bg_color = (0, 0, 0)
        text_color = "white"

    w, h = 1920, 1080

    bg = ColorClip(size=(w, h), duration=dur, color=bg_color)
    txt = TextClip(
        text,
        fontsize=60,
        color=text_color,
        method="caption",
        size=(int(w * 0.8), None),
        align="center",
    ).set_position("center").set_duration(dur).fadein(0.8).fadeout(0.8)

    video = CompositeVideoClip([bg, txt]).set_audio(audio)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    video.write_videofile(str(out_path), fps=30, codec="libx264", audio_codec="aac")


def choose_music(music_style):
    style = music_style.lower()
    candidates = list(ASSETS_MUSIC_DIR.glob("*.mp3")) + list(ASSETS_MUSIC_DIR.glob("*.wav"))

    if not candidates:
        return None

    for f in candidates:
        if any(k in f.stem.lower() for k in style.split()):
            return f
    return candidates[0]


def add_music(video_path, music_path, out_path, vol=0.12):
    video = VideoFileClip(str(video_path))
    voice_audio = video.audio

    music = AudioFileClip(str(music_path)).volumex(vol)

    if music.duration < video.duration:
        loops = (video.duration // music.duration) + 1
        from moviepy.editor import concatenate_audioclips
        music = concatenate_audioclips([music] * int(loops))

    music = music.subclip(0, video.duration)
    final_audio = CompositeAudioClip([voice_audio, music])

    final = video.set_audio(final_audio)
    final.write_videofile(str(out_path), codec="libx264", audio_codec="aac")

def main():
    print("Đang load subplot...")
    plot = load_all_subplots()

    print("Đang gọi Gemini để tạo intro/outro…")
    gem = call_gemini_for_intro_outro(plot)

    tone = gem["tone"]
    intro_text = gem["intro_text"]
    outro_text = gem["outro_text"]
    music_style = gem["music_style"]

    print("Intro:", intro_text)
    print("Outro:", outro_text)
    print("Music:", music_style)

    print("Đang TTS intro/outro...")
    tts = get_tts()
    intro_wav = INTRO_DIR / "intro.wav"
    outro_wav = OUTRO_DIR / "outro.wav"

    tts_to_file(tts, intro_text, intro_wav)
    tts_to_file(tts, outro_text, outro_wav)

    print("Đang tạo video intro/outro...")
    style = "light" if "light" in tone.lower() else "dark"

    intro_mp4 = INTRO_DIR / "intro.mp4"
    outro_mp4 = OUTRO_DIR / "outro.mp4"

    create_text_video(intro_text, intro_wav, intro_mp4, style)
    create_text_video(outro_text, outro_wav, outro_mp4, style)

    print("Đang ghép intro + trailer + outro...")
    intro_clip = VideoFileClip(str(intro_mp4))
    main_clip = VideoFileClip(str(MAIN_TRAILER_PATH))
    outro_clip = VideoFileClip(str(outro_mp4))

    merged = concatenate_videoclips([intro_clip, main_clip, outro_clip], method="compose")

    mid_path = TRAILER_DIR / "trailer_nomusic.mp4"
    merged.write_videofile(str(mid_path), codec="libx264", audio_codec="aac")

    print("Đang thêm nhạc nền...")
    music_file = choose_music(music_style)
    if music_file:
        add_music(mid_path, music_file, FINAL_TRAILER_PATH)
    else:
        mid_path.rename(FINAL_TRAILER_PATH)

    print("Done! Trailer cuối cùng:")
    print(FINAL_TRAILER_PATH)


if __name__ == "__main__":
    main()
