from pathlib import Path
import subprocess
import sys

# Lấy thư mục gốc project (cha của thư mục chứa file này)
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PROJECT = ROOT / "projects" / "LOL"

STEPS = [
    ("Plot retrieval", "plot_retrieval.py"),
    ("Subplot generation", "subplot.py"),
    ("Frame extraction", "frame.py"),
    ("Frame ranking (CLIP)", "image_retrieval.py"),
    ("Voice generation (TTS)", "voice.py"),
    ("Clip creation", "make_clip.py"),
    ("Audio clip creation", "audio_clip.py"),
    ("Final trailer assembly", "join_clip.py"),
]


def ensure_trailers_dir():
    """Chỉ tạo thư mục trailers nếu chưa tồn tại."""
    trailers_dir = PROJECT / "trailers"
    trailers_dir.mkdir(parents=True, exist_ok=True)


def print_progress(step_idx: int, total_steps: int, step_name: str):
    """Hiển thị progress bar đơn giản theo số bước."""
    bar_len = 30
    progress = step_idx / total_steps
    filled = int(bar_len * progress)
    bar = "#" * filled + "-" * (bar_len - filled)
    print(f"\n[{step_idx}/{total_steps}] {step_name}")
    print(f"[{bar}] {progress * 100:5.1f}%\n")


def run_step(step_idx: int, total_steps: int, step_name: str, script_name: str) -> bool:
    print_progress(step_idx, total_steps, step_name)

    script_path = SRC / script_name
    if not script_path.exists():
        print(f"ERROR: Không tìm thấy file: {script_path}")
        return False

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT,
    )

    if result.returncode != 0:
        print(f"ERROR: Lỗi khi chạy {script_name} (exit code {result.returncode})")
        return False

    print(f"Hoàn thành: {step_name}")
    return True


def check_requirements() -> bool:
    """Kiểm tra nhanh một vài input quan trọng."""
    missing = []

    # chỉ cần file plot gốc
    input_plot = PROJECT / "input_plot.txt"
    if not input_plot.exists():
        missing.append("projects/LOL/input_plot.txt")

    # cảnh báo nhẹ nếu thiếu sample_voice (không chặn pipeline)
    sample_voice = ROOT / "voices" / "sample_voice.wav"
    if not sample_voice.exists():
        print("Cảnh báo: Không tìm thấy voices/sample_voice.wav (TTS clone voice có thể không dùng được).")

    if missing:
        print("Thiếu các file sau, vui lòng bổ sung trước khi chạy:")
        for m in missing:
            print(" -", m)
        return False

    return True


def main():
    if not check_requirements():
        return

    ensure_trailers_dir()

    total_steps = len(STEPS)
    for idx, (step_name, script) in enumerate(STEPS, start=1):
        ok = run_step(idx, total_steps, step_name, script)
        if not ok:
            print("Pipeline dừng do lỗi.")
            return

    print("\nPipeline hoàn tất.")
    print("Kiểm tra thư mục: projects/LOL/trailers/")


if __name__ == "__main__":
    main()
