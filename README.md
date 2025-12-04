# Game Trailer Auto Generator 

# Setup Guide
1. Tạo venv ( cho đỡ xung đột thư viện ở máy local )
```bash
python3 -m venv .venv
.venv\Scripts\activate
```
2. 
pip install -r requirements.txt
```bash
pip install -r requirements.txt
export GEMINI_API_KEY="AIzaSyDSSXU67FKHBiH3wcvSC4ZG1NnoXaZjZU0"
```

# Run 
1. Nhập nội dung plot vào game_plot_input.txt ( sẽ update code nếu lấy từ API )
```bash
python src/plot_retrieval.py
```
2. Chia plot thành các subplot (có tóm tắt) bằng Gemini
```bash
python src/subplot.py
```
3. Tạo giọng đọc cho từng plot (Clone theo giọng : voices/sample_voice.wav)
```bash
python src/voice.py
```
