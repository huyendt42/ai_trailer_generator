import logging
import shutil
from pathlib import Path
from TTS.api import TTS
from common import SUBPLOTS_DIR, VOICES_DIR, configs


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)

logger.info("\nStarting voice generation...\n")


def generate_voice(model: TTS, text: str, audio_path: Path, reference_voice: str, language: str) -> None:
    """
    Generate a single TTS audio file using the specified model.
    """
    model.tts_to_file(
        text=text,
        speaker_wav=reference_voice,
        language=language,
        file_path=str(audio_path),
        speed=1.12,
    )


def generate_voices(model: TTS, n_audios: int, reference_voice: str, language: str) -> None:
    """
    Generate audio files for each subplot.
    Subplot text is read from:
        SUBPLOTS_DIR/scene_x/subplot.txt
    Audio is saved to:
        VOICES_DIR/scene_x/audio_1.wav
    """
    
    if VOICES_DIR.exists():
        shutil.rmtree(VOICES_DIR)
    VOICES_DIR.mkdir(parents=True, exist_ok=True)

    for scene_dir in sorted(SUBPLOTS_DIR.glob("scene_*")):
        scene_idx = scene_dir.name  
        subplot_file = scene_dir / "subplot.txt"

        if not subplot_file.exists():
            logger.warning(f"Missing subplot.txt in {scene_dir}, skipping.")
            continue

        scene_text = subplot_file.read_text().strip()
        logger.info(f'Generating audio for {scene_idx}: "{scene_text}"')

        out_dir = VOICES_DIR / scene_idx

        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        for i in range(1, n_audios + 1):
            audio_path = out_dir / f"audio_{i}.wav"
            logger.info(f"Generating audio {i}/{n_audios} for {scene_idx}")
            generate_voice(model, scene_text, audio_path, reference_voice, language)


tts = TTS(model_name=configs["voice"]["model_id"]).to(configs["voice"]["device"])

generate_voices(
    model=tts,
    n_audios=configs["voice"]["n_audios"],
    reference_voice=configs["voice"]["reference_voice_path"],
    language=configs["voice"]["tts_language"],
)

logger.info("\nVoice generation completed successfully.\n")
