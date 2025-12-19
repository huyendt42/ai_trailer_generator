import os
import logging
import shutil
from pathlib import Path
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# --- Giảm load CPU / RAM (đa nền tảng) ---
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from TTS.api import TTS
from common import SUBPLOTS_DIR, VOICES_DIR, configs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)

logger.info("\nStarting voice generation...\n")

# --------------------------------------------------
# Log device đang dùng (quan trọng)
# --------------------------------------------------
device = configs["voice"]["device"]
logger.info(f"[VOICE] Running on device = {device}")

try:
    import torch
    logger.info(
        f"[VOICE] torch={torch.__version__} | "
        f"cuda={torch.cuda.is_available()} | "
        f"mps={hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()}"
    )
    torch.set_num_threads(1)
except Exception as e:
    logger.warning(f"[VOICE] Torch info unavailable: {e}")

# --------------------------------------------------
def generate_voice(
    model: TTS,
    text: str,
    audio_path: Path,
    reference_voice: str,
    language: str,
):
    model.tts_to_file(
        text=text,
        speaker_wav=reference_voice,
        language=language,
        file_path=str(audio_path),
        speed=1.12,
    )

def generate_voices(
    model: TTS,
    n_audios: int,
    reference_voice: str,
    language: str,
):
    VOICES_DIR.mkdir(parents=True, exist_ok=True)

    for scene_dir in sorted(SUBPLOTS_DIR.glob("scene_*")):
        scene_idx = scene_dir.name
        subplot_file = scene_dir / "subplot.txt"

        if not subplot_file.exists():
            logger.warning(f"Missing subplot.txt in {scene_dir}, skipping.")
            continue

        scene_text = subplot_file.read_text().strip()
        logger.info(f'[VOICE] Generating audio for {scene_idx}')

        out_dir = VOICES_DIR / scene_idx
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        for i in range(1, n_audios + 1):
            audio_path = out_dir / f"audio_{i}.wav"
            logger.info(f"[VOICE] Scene {scene_idx} | audio {i}/{n_audios}")
            generate_voice(model, scene_text, audio_path, reference_voice, language)

        # ---- dọn RAM sau mỗi scene ----
        import gc, torch
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            torch.mps.empty_cache()

# --------------------------------------------------
# Load model (CHỈ 1 LẦN)
# --------------------------------------------------
logger.info(f"[VOICE] Loading TTS model: {configs['voice']['model_id']}")
tts = TTS(model_name=configs["voice"]["model_id"]).to(device)

generate_voices(
    model=tts,
    n_audios=configs["voice"]["n_audios"],
    reference_voice=configs["voice"]["reference_voice_path"],
    language=configs["voice"]["tts_language"],
)

logger.info("\nVoice generation completed successfully.\n")