import streamlit as st
from pathlib import Path
import subprocess
import sys

# --- 1. CẤU HÌNH TRANG (LAYOUT WIDE CHO LAPTOP) ---
st.set_page_config(
    page_title="AI TRAILER GENERATOR",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS  ---
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    h1 {
        font-size: 1.8rem !important;
        margin-bottom: 0rem !important;
        color: #FAFAFA;
        border-bottom: 1px solid #333;
        padding-bottom: 10px;
    }

    .stTextArea textarea {
        background-color: #0E1117;
        border: 1px solid #333;
        color: #ddd;
    }
    
    div.stButton > button:first-child {
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ĐƯỜNG DẪN & BIẾN HỆ THỐNG ---
ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / "projects" / "LOL"
VIDEO_PATH = PROJECT / "video_input.mp4"
PLOT_PATH = PROJECT / "input_plot.txt"
TRAILERS = PROJECT / "trailers"
PYTHON = sys.executable

# --- 4. GIAO DIỆN CHÍNH ---

# Tiêu đề nhỏ gọn
st.title("AI Trailer Generator")
st.caption("Made by Duong Thi Huyen, Nguyen Mai Huong, Nguyen Pham Tra My")

# --- KHUNG LÀM VIỆC CHÍNH (Chia 2 cột để vừa màn hình ngang) ---
col_left, col_right = st.columns([5, 6], gap="large")

# === CỘT TRÁI: VIDEO INPUT ===
with col_left:
    st.subheader("1. INPUT VIDEO")
    
    # Upload gọn gàng
    uploaded_video = st.file_uploader(
        "Upload Gameplay (MP4)", 
        type=["mp4"], 
        label_visibility="collapsed"
    )
    
    # Logic lưu và hiện video
    if uploaded_video:
        PROJECT.mkdir(parents=True, exist_ok=True)
        VIDEO_PATH.write_bytes(uploaded_video.read())
        # Hiển thị video preview
        st.video(str(VIDEO_PATH))
    elif VIDEO_PATH.exists():
        st.video(str(VIDEO_PATH))
    else:
        # Placeholder khi chưa có video
        st.info("Waiting for video upload...")

# === CỘT PHẢI: PLOT & ACTIONS ===
with col_right:
    st.subheader("2.INPUT SUBPLOT")
    
    # Text Area nhập Plot
    default_plot = PLOT_PATH.read_text(encoding="utf-8") if PLOT_PATH.exists() else ""
    plot_text = st.text_area(
        "Storyline Script",
        value=default_plot,
        height=320, 
        placeholder="Paste your game plot/story here...",
        label_visibility="collapsed"
    )
    
    c_btn1, c_btn2 = st.columns([1, 2])
    
    with c_btn1:
        if st.button("Save Plot", use_container_width=True):
            PROJECT.mkdir(parents=True, exist_ok=True)
            PLOT_PATH.write_text(plot_text, encoding="utf-8")
            st.toast("Plot saved successfully!")
            
    with c_btn2:
        start_btn = st.button("GENERATE TRAILER", type="primary", use_container_width=True)

# --- 5. LOGIC XỬ LÝ & TIẾN TRÌNH (PROGRESS) ---

st.divider()

if start_btn:
    if not VIDEO_PATH.exists():
        st.error("Missing Video Input")
    elif not plot_text.strip():
        st.error("Missing Plot Text")
    else:
        # Auto-save trước khi chạy
        PROJECT.mkdir(parents=True, exist_ok=True)
        PLOT_PATH.write_text(plot_text, encoding="utf-8")
        with st.status("Processing Pipeline...", expanded=True) as status:
            st.write("Initializing AI Core...")
            
            process = subprocess.Popen(
                [PYTHON, "src/trailer_generator.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=ROOT
            )
            
            log_area = st.empty()
            logs = []
            
            for line in process.stdout:
                logs.append(line)
                log_area.code("".join(logs[-5:]), language="bash")
            
            process.wait()
            
            if process.returncode == 0:
                status.update(label="Generation Completed!", state="complete", expanded=False)
                st.success("Trailer created successfully!")
                
                # --- HIỂN THỊ OUTPUT VIDEO ---
                if TRAILERS.exists():
                    files = sorted(TRAILERS.glob("*.mp4"))
                    if files:
                        latest = files[-1]
                        st.subheader("Final Result")
                        out_c1, out_c2 = st.columns([3, 1])
                        
                        with out_c1:
                            st.video(str(latest))
                        with out_c2:
                            st.write(f"**File:** `{latest.name}`")
                            with open(latest, "rb") as f:
                                st.download_button(
                                    "Download", 
                                    f, 
                                    file_name=latest.name,
                                    use_container_width=True
                                )
            else:
                status.update(label="Generation Failed", state="error", expanded=True)
                st.error("An error occurred. Please check the logs above.")
