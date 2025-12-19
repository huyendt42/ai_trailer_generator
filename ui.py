import streamlit as st
from pathlib import Path
import subprocess
import sys
import os
import signal
import time
import shutil

# --- [FIX FFMPEG] ---
try:
    import imageio_ffmpeg
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    pass

try:
    from pytubefix import YouTube
except ImportError:
    st.error("Thiếu thư viện. Hãy chạy: pip install pytubefix")

# --- 1. CONFIG & THEME ---
st.set_page_config(
    page_title="AI TRAILER STUDIO",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* 1. NỀN CHÍNH (BLACK) */
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
    }
    
    /* 2. HEADER */
    h1, h2, h3 { 
        font-family: 'Helvetica Neue', sans-serif; 
        font-weight: 700; 
        color: #FFFFFF !important;
    }
    
    .hero-text {
        font-size: 2.5rem;
        color: #FFFFFF;
        margin-bottom: 2rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* 3. INPUT FIELDS */
    .stTextInput input, .stTextArea textarea {
        background-color: #021526 !important; /* Nền xanh đen */
        border: 1px solid #03346E !important; /* Viền xanh */
        color: #FFFFFF !important;
        border-radius: 4px;
        font-family: 'Consolas', monospace;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #FFFFFF !important;
        box-shadow: none;
    }

    /* 4. BUTTONS (BLUE #03346E) */
/* 4. BUTTONS & DOWNLOAD BUTTONS (FIXED) */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #03346E !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 4px;
        height: 3.5em;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.2s ease;
        width: 100%;
    }
    
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #0553a0 !important;
        opacity: 0.9;
    }

    /* 5. FILE UPLOADER BUTTON FIX */
    [data-testid="stFileUploader"] button {
        background-color: #03346E !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    [data-testid="stFileUploader"] {
        background-color: #021526;
        border: 1px dashed #03346E;
        border-radius: 4px;
        padding: 10px;
    }

    /* 6. TABS STYLE */
    .stTabs [data-baseweb="tab-list"] { 
        gap: 0px; 
        background-color: transparent;
        border-bottom: 2px solid #03346E;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px; 
        background-color: #000000; 
        color: #666; 
        border: none;
        border-radius: 4px 4px 0 0;
        text-transform: uppercase;
        font-weight: 600;
        font-size: 12px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #03346E !important; 
        color: #FFFFFF !important;
    }
    
    /* 7. TERMINAL / LOG BOX (WHITE TEXT) */
    .terminal-box {
        font-family: 'Consolas', monospace;
        background-color: #000000;
        color: #FFFFFF; /* [EDIT] Chữ trắng theo yêu cầu */
        padding: 15px;
        border: 1px solid #333;
        font-size: 13px;
        line-height: 1.5;
        height: 500px;
        overflow-y: auto;
    }

    /* 8. CONTAINER BORDER */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #021526;
        border: 1px solid #03346E;
        border-radius: 8px;
        padding: 20px;
    }
    
    .stToast { background-color: #021526 !important; border: 1px solid #03346E !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. PATHS & VARS ---
ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / "projects" / "LOL"
VIDEO_PATH = PROJECT / "video_input.mp4"
PLOT_PATH = PROJECT / "input_plot.txt"
TRAILERS = PROJECT / "trailers"
CHECKPOINT_DIR = PROJECT / ".checkpoints"
PYTHON = sys.executable

# --- 3. STATE ---
if 'page' not in st.session_state: st.session_state.page = 'input'
if 'logs' not in st.session_state: st.session_state.logs = [] 
if 'pid' not in st.session_state: st.session_state.pid = None
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'generation_done' not in st.session_state: st.session_state.generation_done = False

# --- 4. HELPERS ---
def clean_workspace():
    paths = [PROJECT / "subplots", PROJECT / "frames", PROJECT / "frames_ranking", 
             PROJECT / "voices", PROJECT / "clips", PROJECT / "audio_clips", 
             PROJECT / "retrieved_plot.txt", PROJECT / "plot.txt", CHECKPOINT_DIR]
    for p in paths:
        if p.exists():
            try: shutil.rmtree(p) if p.is_dir() else p.unlink()
            except: pass

def go_to_processing():
    st.session_state.page = 'processing'
    st.rerun()

def go_to_input():
    st.session_state.page = 'input'
    st.session_state.logs = []
    st.session_state.generation_done = False
    st.session_state.is_running = False
    st.rerun()

# ==========================================
# PAGE 1: INPUT DASHBOARD
# ==========================================
def render_input_page():
    st.markdown('<div class="hero-text">AI TRAILER GENERATOR</div>', unsafe_allow_html=True)
    
    c_media, c_script = st.columns([5, 6], gap="large")

    # --- LEFT: MEDIA SOURCE ---
    with c_media:
        with st.container(border=True):
            st.markdown("### MEDIA SOURCE")
            
            tab1, tab2 = st.tabs(["UPLOAD FILE", "YOUTUBE URL"])
            with tab1:
                st.write("")
                uploaded = st.file_uploader("Select MP4", type=["mp4"], label_visibility="collapsed")
                if uploaded:
                    PROJECT.mkdir(parents=True, exist_ok=True)
                    VIDEO_PATH.write_bytes(uploaded.read())
                    st.toast("Media ready.")
            with tab2:
                st.write("")
                c_url, c_btn = st.columns([3, 1])
                with c_url: yt_url = st.text_input("YouTube URL", label_visibility="collapsed", placeholder="https://youtu.be/...")
                with c_btn:
                    if st.button("GET"):
                        if yt_url:
                            with st.spinner("Fetching..."):
                                try:
                                    PROJECT.mkdir(parents=True, exist_ok=True)
                                    yt = YouTube(yt_url)
                                    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                                    stream.download(output_path=str(PROJECT), filename="video_input.mp4")
                                    st.rerun()
                                except Exception as e: st.error(str(e))

        # Video Preview (Chỉ hiện ở trang Input)
        if VIDEO_PATH.exists():
            st.write("")
            st.video(str(VIDEO_PATH))
        else:
            st.info("Please upload a video to start.")

    # --- RIGHT: SCRIPT & ACTION ---
    with c_script:
        with st.container(border=True):
            st.markdown("### NARRATIVE SCRIPT")
            st.write("")
            
            default_plot = PLOT_PATH.read_text(encoding="utf-8") if PLOT_PATH.exists() else ""
            plot_text = st.text_area("Script", value=default_plot, height=350, placeholder="Paste your storyline here...", label_visibility="collapsed")
            
            st.write("")
            
            c_save, c_run = st.columns([1, 2], gap="small")
            with c_save:
                if st.button("SAVE PLOT"):
                    PROJECT.mkdir(parents=True, exist_ok=True)
                    PLOT_PATH.write_text(plot_text, encoding="utf-8")
                    st.toast("Saved.")
            with c_run:
                if st.button("LAUNCH PIPELINE"):
                    if not VIDEO_PATH.exists() or not plot_text.strip():
                        st.error("Missing Media or Script.")
                    else:
                        PROJECT.mkdir(parents=True, exist_ok=True)
                        PLOT_PATH.write_text(plot_text, encoding="utf-8")
                        clean_workspace()
                        st.session_state.is_running = True
                        st.session_state.logs = []
                        st.session_state.generation_done = False
                        go_to_processing()

# ==========================================
# PAGE 2: PROCESSING CONSOLE
# ==========================================
def render_processing_page():
    st.markdown('<div class="hero-text">PRODUCTION CONSOLE</div>', unsafe_allow_html=True)
    
    # Status Bar
    c_stat, c_ctrl = st.columns([6, 2])
    with c_stat:
        if st.session_state.generation_done: st.success("PIPELINE COMPLETED")
        elif st.session_state.is_running: st.info("PROCESSING IN PROGRESS...")
        else: st.warning("PAUSED")
    with c_ctrl:
        if st.session_state.is_running and not st.session_state.generation_done:
            if st.button("PAUSE"):
                if st.session_state.pid:
                    try: os.kill(st.session_state.pid, signal.SIGTERM)
                    except: pass
                st.session_state.is_running = False
                st.session_state.pid = None
                st.rerun()
        elif not st.session_state.generation_done:
            if st.button("RESUME"):
                st.session_state.is_running = True
                st.rerun()
    
    # Terminal Log (Không hiện video input ở đây)
    with st.container(border=True):
        st.markdown("### SYSTEM LOGS")
        log_box = st.empty()
        if st.session_state.logs:
            log_box.markdown(f'<div class="terminal-box">{"<br>".join(st.session_state.logs)}</div>', unsafe_allow_html=True)
        else:
            log_box.markdown('<div class="terminal-box">Initializing...</div>', unsafe_allow_html=True)

    # Runner
    if st.session_state.is_running and not st.session_state.generation_done:
        process = subprocess.Popen([PYTHON, "src/trailer_generator.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT)
        st.session_state.pid = process.pid
        
        ALLOWED = ["---", "STEP", "Phase", "RUNNING", "SKIPPED", "DONE", "FAILED", "FINISHED", "ERROR",
                   "Trailer created", "Rendering", "Scene", "Saved", "Generating", "AI Selected", "Mixed", "Detecting", "Retrieving", "Loading", "Collected", "Joining"]

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None: break
            if line:
                clean = line.strip()
                if not clean: continue
                if any(m in clean for m in ALLOWED):
                    st.session_state.logs.append(clean)
                    js = f"""<div class="terminal-box" id="term">{"<br>".join(st.session_state.logs)}<script>var d=document.getElementById("term");d.scrollTop=d.scrollHeight;</script></div>"""
                    log_box.markdown(js, unsafe_allow_html=True)
        
        st.session_state.is_running = False
        st.session_state.pid = None
        if process.returncode == 0:
            st.session_state.generation_done = True
            st.rerun()

    # Result (Chỉ hiện khi xong)
    if st.session_state.generation_done:
        st.divider()
        if TRAILERS.exists():
            files = sorted(TRAILERS.glob("*.mp4"))
            if files:
                latest = files[-1]
                c1, c2 = st.columns([2, 1])
                with c1: st.video(str(latest))
                with c2:
                    with st.container(border=True):
                        st.markdown("### RESULT")
                        st.write(f"`{latest.name}`")
                        with open(latest, "rb") as f:
                            st.download_button("DOWNLOAD MP4", f, file_name=latest.name, mime="video/mp4")
                        st.write("")
                        if st.button("START NEW PROJECT"): go_to_input()
                    
# MAIN ROUTER
if st.session_state.page == 'input': render_input_page()
elif st.session_state.page == 'processing': render_processing_page()
