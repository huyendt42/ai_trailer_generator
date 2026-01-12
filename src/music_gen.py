import sys
import logging
from pathlib import Path
import torch
import scipy.io.wavfile
import numpy as np 

# --- 1. KIỂM TRA THƯ VIỆN ---
try:
    from transformers import pipeline
except ImportError:
    print("ERROR: Missing libraries. Run: pip install transformers scipy torch numpy")
    sys.exit(1)

# --- CẤU HÌNH ---
ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "projects" / "LOL"
PROMPT_PATH = PROJECT_DIR / "music_prompt.txt"
OUTPUT_PATH = PROJECT_DIR / "background_music.wav"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MusicGen")

def main():
    logger.info("--- STARTING MUSIC GENERATION (Fixed Shape) ---")

    # 1. Đọc Prompt
    prompt = "Cinematic game trailer music, epic, orchestral" 
    if PROMPT_PATH.exists():
        text = PROMPT_PATH.read_text(encoding="utf-8").strip()
        if text: prompt = text
    
    logger.info(f"Prompt: {prompt}")

    # 2. Quản lý Device (GPU/CPU)
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        device = 0
        logger.info("Device: GPU (Fast)")
    else:
        device = -1
        logger.info("Device: CPU (Slower)")

    try:
        # 3. Load Model
        synthesiser = pipeline("text-to-audio", "facebook/musicgen-small", device=device)

        # 4. Sinh nhạc
        logger.info("Generating sample...")
        music = synthesiser(
            prompt, 
            forward_params={"do_sample": True, "max_new_tokens": 512}
        )

        # 5. XỬ LÝ DỮ LIỆU
        sampling_rate = music["sampling_rate"]
        audio_data = np.array(music["audio"][0]) 

        if len(audio_data.shape) > 1:
            audio_data = audio_data.squeeze()

        # Chuẩn hóa biên độ về [-1, 1]
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        audio_data_int16 = (audio_data * 32767).astype(np.int16)
        
        # 6. Lưu file
        scipy.io.wavfile.write(str(OUTPUT_PATH), rate=sampling_rate, data=audio_data_int16)
        logger.info(f"SUCCESS: Music saved to {OUTPUT_PATH}")

    except Exception as e:
        logger.error(f"Generation Failed: {e}")
        import traceback
        traceback.print_exc() # In chi tiết lỗi để debug nếu cần
        sys.exit(1)

if __name__ == "__main__":
    main()
