# Firebase 部署步驟指南

## 目前完成狀態
程式碼遷移已完成：
- `main.py` — `_sessions` 字典已改為 Firestore 持久化
- `requirements.txt` — 已加入 `firebase-admin`, `google-cloud-firestore`, `asgiref`
- `firebase.json` — Firebase Hosting + Cloud Run rewrite 設定
- `config/firebase/firestore.rules` — 僅允許伺服器端存取 (路徑已更新)

---

## 注意事項（部署前）

### Firebase 設定
`firebase.json` 已更新為指向 `config/firebase/firestore.rules`。若您手動修改了目錄結構，請確保 `firebase.json` 中的 `firestore.rules` 路徑正確。
目前 `Dockerfile` 使用 port **7860**（Hugging Face 格式），Cloud Run 預設需要 **8080**。
部署前需修改 `Dockerfile` 最後一行：
```dockerfile
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
```

---

## 部署步驟

### 步驟 1 — 安裝工具（如未安裝）
```bash
# Firebase CLI
npm install -g firebase-tools

# Google Cloud CLI
# 至 https://cloud.google.com/sdk/docs/install 下載安裝
```

### 步驟 2 — 登入 Firebase
```bash
firebase login
```

### 步驟 3 — 建立 / 確認 GCP 專案
```bash
# 查看現有專案
gcloud projects list

# 或建立新專案（將 YOUR_PROJECT_ID 換成自訂 ID）
gcloud projects create YOUR_PROJECT_ID

# 設定預設專案
gcloud config set project YOUR_PROJECT_ID
```
> 需至 GCP Console 啟用計費（升級為 Blaze Plan）才能使用 Cloud Run 和 Firestore。

### 步驟 4 — 啟用必要 API
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable firestore.googleapis.com
```

### 步驟 5 — 初始化 Firebase 專案
```bash
firebase init
# 選擇：Firestore、Hosting
# Hosting public directory：public_placeholder
# 綁定到你的 GCP 專案
```

### 步驟 6 — 建置並推送 Docker Image
```bash
# 使用 Cloud Build（不需本地 Docker）
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/downloader-api
```

### 步驟 7 — 部署到 Cloud Run
```bash
gcloud run deploy downloader-api \
  --image gcr.io/YOUR_PROJECT_ID/downloader-api \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --set-env-vars CULROC_USERNAME=201,CULROC_PASSWORD=a0980463
```
> 環境變數 `CULROC_USERNAME` 和 `CULROC_PASSWORD` 取代本地 `.env` 檔案。

### 步驟 8 — 部署 Firebase Hosting
```bash
firebase deploy --only hosting
```

---

## 完成後的架構
```
用戶瀏覽器
    ↓
Firebase Hosting (CDN)
    ↓ rewrite **
Cloud Run (downloader-api)
    ↓ 存取 session
Firestore (sessions collection)
```

---

## 常見問題

| 問題 | 解法 |
|------|------|
| Cloud Run 回應 403 | 確認 `--allow-unauthenticated` 有加 |
| Firestore 權限錯誤 | Cloud Run 服務帳號需有 `roles/datastore.user` 權限 |
| Port 錯誤 / 容器無法啟動 | Dockerfile 的 port 改為 8080 |
| `.env` 憑證不生效 | 用 `--set-env-vars` 傳入，不要把 `.env` 打包進 image |
