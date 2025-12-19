import sys
import subprocess
from pathlib import Path
import shutil

# --- CẤU HÌNH ---
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PROJECT = ROOT / "projects" / "LOL"
CHECKPOINT_DIR = PROJECT / ".checkpoints" 

# ĐỊNH NGHĨA QUY TRÌNH
STEPS = [
    {"name": "Phase 1: Plot Retrieval", "script": "plot_retrieval.py"},
    {"name": "Phase 2: Subplot Generation", "script": "subplot.py"},
    {"name": "Phase 3: Frame Extraction", "script": "frame.py"},
    {"name": "Phase 4: Frame Ranking", "script": "image_retrieval.py"},
    {"name": "Phase 5: Voice Gen", "script": "voice.py"},
    {"name": "Phase 6: Clip Creation", "script": "make_clip.py"},
    {"name": "Phase 7: Audio Mixing", "script": "audio_clip.py"},
    {"name": "Phase 8: Final Assembly", "script": "join_clip.py"} 
]

def run_pipeline():
    python_exe = sys.executable
    print("--- PIPELINE ORCHESTRATOR STARTED ---")
    sys.stdout.flush()
    
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    
    total = len(STEPS)
    start_index = 0
    
    for i, step in enumerate(STEPS):
        marker_name = f"{i+1}_{step['script']}.done"
        marker_path = CHECKPOINT_DIR / marker_name
        
        if marker_path.exists():
            print(f"[STEP {i+1}/{total}] SKIPPED: {step['name']} (Completed)")
            start_index = i + 1
        else:
            break 
            
    sys.stdout.flush()

    for i in range(start_index, total):
        step = STEPS[i]
        script_name = step["script"]
        step_name = step["name"]
        
        marker_name = f"{i+1}_{script_name}.done"
        marker_path = CHECKPOINT_DIR / marker_name
        
        print(f"[STEP {i+1}/{total}] RUNNING: {step_name}...")
        sys.stdout.flush()
        
        script_path = SRC / script_name
        if not script_path.exists():
            print(f"ERROR: Missing script {script_name}")
            sys.exit(1)
            
        try:
            subprocess.run([python_exe, str(script_path)], cwd=ROOT, check=True, text=True)
            marker_path.touch()
            print(f"[STEP {i+1}/{total}] DONE: {step_name}")
            
        except subprocess.CalledProcessError:
            print(f"FAILED at {step_name}")
            if marker_path.exists(): marker_path.unlink()
            sys.exit(1)
            
    print("--- PIPELINE FINISHED SUCCESSFULLY ---")
    sys.stdout.flush()

if __name__ == "__main__":
    run_pipeline()
