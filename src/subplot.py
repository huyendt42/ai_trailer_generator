import logging
import json
import os
from pathlib import Path

import google.generativeai as genai

from common import PROJECT_DIR, SUBPLOTS_DIR, configs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)

PLOT_PATH = PROJECT_DIR / "plot.txt"


def generate_subplots_with_gemini(plot: str, n_subplots: int = 6) -> list[str]:
    """Generate cinematic subplots from main plot using Gemini API."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("models/gemini-2.5-flash")

    prompt = (
        f"Split the following game plot into {n_subplots} cinematic trailer subplots.\n"
        "Each subplot should be 2-3 descriptive sentences suitable for trailer voice-over.\n"
        "Return ONLY the list of subplots, each starting with '- '.\n\n"
        f"GAME PLOT:\n{plot}"
    )

    logger.info("Calling Gemini to generate subplots...")
    response = model.generate_content(prompt)
    text = response.text

    # Parse subplots
    subplots = [line[2:].strip() for line in text.split("\n") if line.strip().startswith("-")]
    logger.info("Generated %d subplots", len(subplots))

    return subplots


def save_subplots(subplots: list[str]) -> None:
    """Save each subplot to projects/LOL/subplots/scene_i/subplot.txt"""
    SUBPLOTS_DIR.mkdir(parents=True, exist_ok=True)

    for idx, subplot in enumerate(subplots, start=1):
        scene_dir = SUBPLOTS_DIR / f"scene_{idx}"
        scene_dir.mkdir(parents=True, exist_ok=True)
        subplot_path = scene_dir / "subplot.txt"
        subplot_path.write_text(subplot, encoding="utf-8")
        logger.info("Saved subplot %d to %s", idx, subplot_path)

    # Save full list
    json_path = SUBPLOTS_DIR / "subplots.json"
    json_path.write_text(json.dumps(subplots, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    if not PLOT_PATH.exists():
        raise FileNotFoundError(f"plot.txt not found at {PLOT_PATH}")

    logger.info("Reading plot from %s", PLOT_PATH)
    plot_text = PLOT_PATH.read_text(encoding="utf-8")

    n_subplots = configs["subplot"]["n_subplots"]

    subplots = generate_subplots_with_gemini(plot_text, n_subplots=n_subplots)

    save_subplots(subplots)


if __name__ == "__main__":
    main()
