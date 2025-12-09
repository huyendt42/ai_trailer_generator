import logging
import shutil
import json
import os
import time
from pathlib import Path

# Sử dụng thư viện ổn định (google-generativeai)
import google.generativeai as genai
from google.api_core import exceptions

from common import PROJECT_DIR, SUBPLOTS_DIR, configs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PLOT_PATH = PROJECT_DIR / "plot.txt"

def get_best_available_model():
    """
    Tự động lấy danh sách model khả dụng từ Google và chọn cái tốt nhất.
    """
    try:
        logger.info("Đang kết nối Google để lấy danh sách model...")
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        logger.info(f"Các model tìm thấy: {available_models}")
        
        # Danh sách ưu tiên (Model ổn định trước)
        priorities = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-pro",
            "models/gemini-pro",
            "models/gemini-1.0-pro"
        ]
        
        for p in priorities:
            if p in available_models:
                logger.info(f"-> Đã chọn model: {p}")
                return p
        
        # Fallback
        if available_models:
            first = available_models[0]
            logger.warning(f"Không có model ưu tiên, dùng tạm: {first}")
            return first
            
        raise RuntimeError("Không tìm thấy model nào hỗ trợ generateContent.")

    except Exception as e:
        logger.error(f"Lỗi khi dò tìm model: {e}")
        return "models/gemini-pro"

def generate_with_retry(model, prompt, retries=3):
    """
    Cơ chế thử lại khi bị lỗi Quota (429)
    """
    for attempt in range(retries + 1):
        try:
            response = model.generate_content(prompt)
            return response.text
        except exceptions.ResourceExhausted:
            # Lỗi 429: Hết lượt gọi -> Chờ và thử lại
            wait_time = 30 * (attempt + 1)
            logger.warning(f"⚠️ Hết Quota (429). Đang nghỉ {wait_time}s rồi thử lại...")
            time.sleep(wait_time)
            continue
        except Exception as e:
            logger.error(f"Lỗi API: {e}")
            raise e
            
    raise RuntimeError("Đã hết số lần thử lại (Max Retries).")

def generate_subplots_with_gemini(plot: str, n_subplots: int = 6) -> list[str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = configs.get("gemini_api_key")
    if not api_key:
        raise RuntimeError("Thiếu GEMINI_API_KEY.")

    genai.configure(api_key=api_key)

    # 1. Tự chọn model
    model_name = get_best_available_model()
    model = genai.GenerativeModel(model_name)

    prompt = f"""
    You are a scriptwriter. Break the following plot into exactly {n_subplots} cinematic scenes.
    
    Requirements:
    - Output ONLY a JSON array of strings.
    - Each string is a short description of a scene.
    - No markdown, no "json" tags, no extra text.
    
    PLOT:
    {plot}
    """

    logger.info(f"Gửi lệnh cho model {model_name}...")
    
    # 2. Gọi API với cơ chế retry
    text = generate_with_retry(model, prompt)
    
    # 3. Xử lý kết quả
    text = text.strip()
    if text.startswith("```json"): text = text[7:]
    if text.endswith("```"): text = text[:-3]
    text = text.strip()

    try:
        subplots = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Lỗi parse JSON, đang thử cắt dòng thủ công...")
        subplots = [line for line in text.split("\n") if line.strip()]

    return subplots[:n_subplots]

def save_scenes(subplots: list[str]):
    if SUBPLOTS_DIR.exists():
        shutil.rmtree(SUBPLOTS_DIR)
    SUBPLOTS_DIR.mkdir(parents=True, exist_ok=True)

    for idx, subplot in enumerate(subplots, start=1):
        scene_dir = SUBPLOTS_DIR / f"scene_{idx}"
        scene_dir.mkdir(parents=True, exist_ok=True)
        
        (scene_dir / "subplot.txt").write_text(subplot, encoding="utf-8")
        logger.info(f"Saved scene {idx}")

    (SUBPLOTS_DIR / "subplots.json").write_text(
        json.dumps(subplots, indent=2, ensure_ascii=False), encoding="utf-8"
    )

def main():
    if not PLOT_PATH.exists():
        # Tạo file giả nếu chưa có để test
        PLOT_PATH.write_text("Test plot content", encoding="utf-8")

    plot_text = PLOT_PATH.read_text(encoding="utf-8").strip()
    if not plot_text:
        raise ValueError("File plot.txt bị trống.")

    n_subplots = configs.get("subplot", {}).get("n_subplots", 6)

    subplots = generate_subplots_with_gemini(plot_text, n_subplots)
    save_scenes(subplots)

    logger.info("\nDONE: Đã tạo kịch bản thành công.\n")

if __name__ == "__main__":
    main()