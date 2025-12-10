# Game Trailer Auto Generator 

# Setup Guide

1. Tạo venv (cho đỡ xung đột thư viện ở máy local)
   
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

2. Cài đặt thư viện
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --no-cache-dir
   ```

3. Cấu hình API Key (Gemini)
   ```bash
   # Linux / macOS
   export GEMINI_API_KEY="YOUR_API_KEY_HERE"
   
   # Windows (CMD)
   set GEMINI_API_KEY="YOUR_API_KEY_HERE"
   
   # Windows (PowerShell)
   $env:GEMINI_API_KEY="YOUR_API_KEY_HERE"
   ```

# Run 

### Cách 1: Giao diện Web (Khuyên dùng)
```bash
streamlit run ui.py
```

### Cách 2: Chạy dòng lệnh (CLI)

1. Nhập nội dung plot vào `game_plot_input.txt` (sẽ update code nếu lấy từ API)
   ```bash
   python src/plot_retrieval.py
   ```

2. Chia plot thành các subplot (có tóm tắt) bằng Gemini
   ```bash
   python src/subplot.py
   ```

3. Xử lý video đầu vào (Cắt scene)
   ```bash
   python src/video_retrieval.py
   ```

4. Tạo giọng đọc cho từng plot (Clone theo giọng: `voices/sample_voice.wav`)
   ```bash
   python src/voice.py
   ```

5. Ghép các clip lại thành Trailer hoàn chỉnh
   ```bash
   python src/join_clip.py
   ```

# Troubleshooting (Lỗi thường gặp)

* **Lỗi `OSError: [Errno 28] No space left on device`**: Ổ cứng đầy, cần dọn dẹp khoảng 5GB.
* **Lỗi `Weights only load failed`**: Do bản PyTorch 2.6 mới quá. Cần cài lại bản 2.4.0.
* **Lỗi MoviePy**: Đảm bảo đang dùng `moviepy==1.0.3` trong requirements.txt.
