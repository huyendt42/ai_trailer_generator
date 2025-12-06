import streamlit as st
from pathlib import Path
import subprocess
import sys

# Page config must be the first streamlit command
st.set_page_config(page_title="LOL Trailer Generator", layout="centered")

# Define paths (Assuming ui.py is in the Project Root)
ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / "projects" / "LOL"
VIDEO_PATH = PROJECT / "video_input.mp4"
PLOT_PATH = PROJECT / "input_plot.txt"
TRAILERS = PROJECT / "trailers"

PYTHON = sys.executable

st.title("LOL Trailer Generator")

# --- SECTION 1: VIDEO UPLOAD ---
st.header("1. Upload Video Input (MP4)")
uploaded_video = st.file_uploader("Upload MP4 file:", type=["mp4"])

if uploaded_video:
    # Ensure directory exists
    PROJECT.mkdir(parents=True, exist_ok=True)
    
    # Save the file
    VIDEO_PATH.write_bytes(uploaded_video.read())
    st.success(f"Video saved to: {VIDEO_PATH}")

# --- SECTION 2: PLOT INPUT ---
st.header("2. Enter Plot Text")

# Load existing plot if available
default_plot = PLOT_PATH.read_text(encoding="utf-8") if PLOT_PATH.exists() else ""

plot_text = st.text_area(
    "Plot text (Paste your story here):",
    value=default_plot,
    height=300
)

# Manual save button
if st.button("Save Plot"):
    PROJECT.mkdir(parents=True, exist_ok=True)
    PLOT_PATH.write_text(plot_text, encoding="utf-8")
    st.success("Plot saved manually!")

# --- SECTION 3: GENERATION ---
st.header("3. Generate Trailer")
run_button = st.button("Start Trailer Generation", type="primary")

if run_button:
    # AUTO-SAVE: Save the text currently in the text area to the file
    if plot_text.strip():
        PROJECT.mkdir(parents=True, exist_ok=True)
        PLOT_PATH.write_text(plot_text, encoding="utf-8")
        st.info("Auto-saved latest plot text.")

    # Validation
    if not VIDEO_PATH.exists():
        st.error("Error: Video file not found. Please upload a video.")
    elif not PLOT_PATH.exists() or not plot_text.strip():
        st.error("Error: Plot text is missing.")
    else:
        st.info("Starting pipeline... Please wait, this may take several minutes.")

        # Run the backend pipeline
        process = subprocess.Popen(
            [PYTHON, "src/trailer_generator.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=ROOT  # Run from root so src/ imports work
        )

        # Live log streaming
        log_area = st.empty()
        logs = ""

        for line in process.stdout:
            logs += line
            log_area.text(logs)  # Update log window

        process.wait()

        if process.returncode == 0:
            st.success("Trailer generation completed!")
            
            # Check for output file
            if TRAILERS.exists():
                mp4s = sorted(TRAILERS.glob("*.mp4"))
                if mp4s:
                    latest_video = mp4s[-1]
                    st.video(str(latest_video))
                    
                    with open(latest_video, "rb") as file:
                        st.download_button(
                            label="Download Trailer",
                            data=file,
                            file_name=latest_video.name,
                            mime="video/mp4"
                        )
                else:
                    st.warning("Pipeline finished, but no MP4 file was found in 'trailers/'.")
            else:
                st.warning("Trailers directory does not exist.")
        else:
            st.error("An error occurred during pipeline execution. Check logs above.")