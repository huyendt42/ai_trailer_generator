import streamlit as st
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / "projects" / "LOL"
VIDEO_PATH = PROJECT / "video_input.mp4"
PLOT_PATH = PROJECT / "input_plot.txt"
TRAILERS = PROJECT / "trailers"

PYTHON = sys.executable
st.set_page_config(page_title="LOL Trailer Generator", layout="centered")
st.title("LOL Trailer Generator")
st.header("1. Upload Video Input (MP4)")

uploaded_video = st.file_uploader("Upload MP4 file:", type=["mp4"])

if uploaded_video:
    VIDEO_PATH.write_bytes(uploaded_video.read())
    st.success(f"Video saved to {VIDEO_PATH}")
st.header("2. Enter Plot Text")

default_plot = PLOT_PATH.read_text() if PLOT_PATH.exists() else ""

plot_text = st.text_area(
    "Plot text (use long multi-paragraph story like your Yunara sample):",
    value=default_plot,
    height=360
)

if st.button("Save Plot"):
    PLOT_PATH.write_text(plot_text)
    st.success("Plot saved!")
st.header("3. Generate Trailer")
run_button = st.button("Start Trailer Generation", type="primary")

if run_button:
    if not VIDEO_PATH.exists():
        st.error("You must upload a video file.")
    elif not PLOT_PATH.exists():
        st.error("Missing input_plot.txt. Please save your plot first.")
    else:
        st.info("Running trailer pipeline… this may take several minutes.")

        # Run pipeline
        process = subprocess.Popen(
            [PYTHON, "src/trailer_generator.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=ROOT  # IMPORTANT: run from root
        )

        # Live logs
        log_area = st.empty()
        logs = ""

        for line in process.stdout:
            logs += line
            log_area.text(logs)

        process.wait()

        if process.returncode == 0:
            st.success("Trailer generation completed successfully!")

            # Find latest trailer
            if TRAILERS.exists():
                mp4s = sorted(TRAILERS.glob("*.mp4"))
                if mp4s:
                    latest = mp4s[-1]
                    st.video(str(latest))
                    st.download_button(
                        "Download Trailer",
                        data=latest.read_bytes(),
                        file_name=latest.name
                    )
                else:
                    st.warning("No trailer files found.")
            else:
                st.warning("Trailer folder does not exist.")
        else:
            st.error("Error during pipeline execution.")
