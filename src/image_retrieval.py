import logging
import shutil
from pathlib import Path
from multiprocessing import Pool, cpu_count

import torch
from PIL import Image
from sentence_transformers import SentenceTransformer, util

from common import (
    FRAMES_RANKING_DIR,
    FRAMES_DIR,
    SUBPLOTS_DIR,
    configs,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)

def load_model():
    model_id = configs["frame_ranking"]["model_id"]  # "clip-ViT-L-14"
    device = configs["frame_ranking"]["device"]      # "cuda" or "cpu"

    logger.info(f"Loading CLIP model: {model_id} on {device}")

    model = SentenceTransformer(model_id, device=device)
    return model

def collect_all_frames():
    """Collect all frames from frames/scene_x."""
    frame_paths = []

    for scene_dir in sorted(FRAMES_DIR.glob("scene_*"), key=lambda x: int(x.name.split("_")[1])):
        for img in sorted(scene_dir.glob("*.jpg")):
            frame_paths.append(img)

    logger.info(f"Collected {len(frame_paths)} frames.")
    return frame_paths

def load_image(path: Path):
    try:
        return Image.open(path).convert("RGB")
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        return None

def embed_images(frame_paths, model, batch_size):
    logger.info(f"Loading {len(frame_paths)} images in parallel...")

    num_workers = max(2, cpu_count() // 2)

    with Pool(processes=num_workers) as pool:
        loaded_imgs = list(pool.map(load_image, frame_paths))

    valid_pairs = [(img, path) for img, path in zip(loaded_imgs, frame_paths) if img is not None]

    if not valid_pairs:
        raise RuntimeError("No valid frames found to embed.")

    imgs, valid_paths = zip(*valid_pairs)
    imgs = list(imgs)
    valid_paths = list(valid_paths)

    logger.info(f"Valid frames: {len(imgs)}. Starting CLIP embedding...")

    all_embs = []

    for i in range(0, len(imgs), batch_size):
        batch = imgs[i:i + batch_size]
        emb = model.encode(batch, convert_to_tensor=True, batch_size=batch_size, show_progress_bar=False)
        all_embs.append(emb)

    frame_emb = torch.cat(all_embs, dim=0)
    logger.info(f"Created {frame_emb.shape[0]} embeddings.")

    return frame_emb, valid_paths


def embed_text(query, model):
    return model.encode([query], convert_to_tensor=True, show_progress_bar=False)

def retrieve_best_frames(query, model, frame_emb, frame_paths, top_k):
    q_emb = embed_text(query, model)
    hits = util.semantic_search(q_emb, frame_emb, top_k=top_k)[0]

    return [(hit["score"], frame_paths[hit["corpus_id"]]) for hit in hits]

def process_all_subplots(model, frame_emb, frame_paths):
    top_k = configs["frame_ranking"]["n_retrieved_images"]

    if FRAMES_RANKING_DIR.exists():
        shutil.rmtree(FRAMES_RANKING_DIR)
    FRAMES_RANKING_DIR.mkdir(parents=True, exist_ok=True)

    subplot_files = sorted(SUBPLOTS_DIR.glob("scene_*/*.txt"),
                           key=lambda p: int(p.parent.name.split("_")[1]))

    for subplot_file in subplot_files:
        text = subplot_file.read_text().strip()
        scene_name = subplot_file.parent.name

        logger.info(f"Retrieving frames for: {scene_name}")

        ranked = retrieve_best_frames(text, model, frame_emb, frame_paths, top_k)

        out_dir = FRAMES_RANKING_DIR / scene_name
        out_dir.mkdir(parents=True, exist_ok=True)

        for score, frame_path in ranked:
            score_str = f"{score:.4f}"
            out_path = out_dir / f"{score_str}_{frame_path.name}"
            shutil.copy(frame_path, out_path)

if __name__ == "__main__":
    logger.info("\nStarting Frame Retrieval Pipeline\n")

    model = load_model()

    all_frames = collect_all_frames()

    batch_size = configs["frame_ranking"]["similarity_batch_size"]
    frame_emb, valid_frame_paths = embed_images(all_frames, model, batch_size)

    process_all_subplots(model, frame_emb, valid_frame_paths)

    logger.info("\n##### Frame Retrieval Completed Successfully #####\n")
