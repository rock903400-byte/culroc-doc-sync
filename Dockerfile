# 使用 Python 3.12 映像檔
FROM python:3.12-slim

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案（包含 templates）
COPY . .

# Hugging Face Spaces 預設會偵測 7860 連接埠
# 我們將 FastAPI 運行在 7860
EXPOSE 8080

# 啟動指令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
