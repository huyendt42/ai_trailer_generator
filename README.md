# 🎬 Game Trailer Auto Generator

Công cụ tự động tạo trailer game từ video gameplay và cốt truyện sử dụng AI (Gemini LLM & CLIP Model).

---

## 🛠️ Setup Guide (Cài đặt)

### 1. Cài đặt FFmpeg (BẮT BUỘC)
Hệ thống cần FFmpeg để xử lý video và âm thanh.
* **Windows:** Tải [FFmpeg](https://ffmpeg.org/download.html), giải nén và thêm đường dẫn `bin` vào Environment Variables (PATH).
* **Linux (Ubuntu):**
    ```bash
    sudo apt update
    sudo apt install ffmpeg
    ```
* **macOS:**
    ```bash
    brew install ffmpeg
    ```

### 2. Tạo môi trường ảo (Virtual Environment)
Giúp tránh xung đột thư viện với hệ thống chính.

* **Windows:**
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```

* **Linux / macOS:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

### 3. Cài đặt thư viện Python
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
