import logging
from pathlib import Path

from common import PROJECT_DIR, configs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)

logger.info("\nStarting plot retrieval (MANUAL GAME MODE)\n")

# Đường dẫn file plot output mới
PLOT_PATH = PROJECT_DIR / "plot.txt"


def get_manual_plot() -> str:
    """
    Read the manually provided game plot from 'manual_plot.txt'
    located in the project directory.
    """

    manual_file = PROJECT_DIR / "manual_plot.txt"

    if not manual_file.exists():
        raise FileNotFoundError(
            f"manual_plot.txt not found at:\n  {manual_file}\n"
            "→ Please create this file and paste your game plot into it."
        )

    logger.info(f"Reading manual plot from: {manual_file}")
    text = manual_file.read_text(encoding="utf-8").strip()

    if not text:
        raise ValueError(f"The file {manual_file} is empty. Please insert the game plot text.")

    return text


# Tạo thư mục project nếu cần
if not PROJECT_DIR.exists():
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)

# Lấy config nguồn plot (dù hiện tại chỉ hỗ trợ manual)
plot_cfg = configs.get("plot_retrieval", {})
source = plot_cfg.get("source", "manual")

if source != "manual":
    logger.warning(
        f"plot_retrieval.source = '{source}' is not supported. Falling back to manual mode."
    )

# Đọc và lưu plot
plot_text = get_manual_plot()

logger.info(f"Saving plot to: {PLOT_PATH}")
PLOT_PATH.write_text(plot_text, encoding="utf-8")

logger.info("\nPlot retrieval completed successfully\n")
