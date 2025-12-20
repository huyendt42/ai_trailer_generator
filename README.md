# Game Trailer Auto Generator

An AI-powered system that automatically generates cinematic game trailers from gameplay footage and narrative plots using Large Language Models (Gemini) and Vision-Language Models (CLIP).

## Setup Guide

### 1. Install FFmpeg (Required)
The system requires FFmpeg for video and audio processing.
* **Windows:** Download FFmpeg, extract it, and add the `bin` folder to your System PATH variables.
* **Linux (Ubuntu/Debian):** `sudo apt update && sudo apt install ffmpeg`
* **macOS:** `brew install ffmpeg`

### 2. Create Virtual Environment
Create an isolated environment to prevent library conflicts.

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### 4. Configure API Key
Set up your Google Gemini API key.

**Linux / macOS:**
```bash
export GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

**Windows (CMD):**
```cmd
set GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

## Usage

### Method 1: Web Interface (Recommended)
Launch the graphical user interface to upload videos and monitor progress visually.
```bash
streamlit run ui.py
```

### Method 2: CLI Automation (Orchestrator)
Run the full pipeline sequentially using the orchestration script. This includes checkpoint recovery support.
```bash
python src/trailer_generator.py
```

### Method 3: Manual Execution
Run each step individually for debugging purposes. Ensure `projects/LOL/video_input.mp4` exists before starting.

1. **Plot Retrieval** (Fetch or process input plot):
   ```bash
   python src/plot_retrieval.py
   ```

2. **Subplot Generation** (Segment plot into narrative scenes using Gemini):
   ```bash
   python src/subplot.py
   ```

3. **Frame Extraction** (Detect scenes and extract keyframes from video):
   ```bash
   python src/frame.py
   ```

4. **Frame Ranking** (Rank frames against subplots using CLIP):
   ```bash
   python src/image_retrieval.py
   ```

5. **Voice Generation** (Generate TTS audio for each subplot):
   ```bash
   python src/voice.py
   ```

6. **Clip Creation** (Cut video segments based on ranked frames):
   ```bash
   python src/make_clip.py
   ```

7. **Audio Mixing** (Process and mix audio tracks):
   ```bash
   python src/audio_clip.py
   ```

8. **Final Assembly** (Merge all clips into the final trailer):
   ```bash
   python src/join_clip.py
   ```

## Troubleshooting

* **OSError: [Errno 28] No space left on device:** The process generates many temporary image files. Ensure you have at least 5GB of free disk space.
* **Weights only load failed:** This may occur if using a newer PyTorch version with older models. Downgrade to a stable version:
  ```bash
  pip install torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0
  ```
* **MoviePy Errors:** Ensure you are using a compatible version of MoviePy:
  ```bash
  pip install moviepy==1.0.3
  ```
* **Checkpoint Errors:** If the pipeline gets stuck, delete the `.checkpoints` folder inside `projects/LOL/` to restart the process cleanly.
