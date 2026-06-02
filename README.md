# 文件下載代理系統 (Mobile-Friendly Web Downloader)

這是一個專為行動裝置設計的網頁代理工具，主要用於登入並下載 `http://www.culroc.org.tw/cu/` 網站上的檔案。系統具備強大的自動化爬蟲能力，能解析動態生成的檔案清單，並提供友善的搜尋與過濾介面。

## 🌟 核心功能

*   **動態檔案爬取**：自動解析網站 JavaScript 動態生成的 `aData` 變數，支援超過 500 個檔案下載。
*   **訪客一鍵登入**：支援後端預設憑證，使用者無需手動輸入帳號密碼即可登入。
*   **進階列表顯示**：包含檔案名稱、類別、上傳日期及備註說明。
*   **搜尋與過濾**：可依關鍵字搜尋或依業務類別過濾檔案，快速定位目標。
*   **行動裝置優化**：基於 Bootstrap 5 構建，具備完整的響應式設計，適合手機操作。
*   **連線穩定性修復**：解決了伺服器端連線中斷（Connection Aborted）與損壞重定向網址的問題。
*   **Firebase 整合**：支援將檔案同步至 Firebase Storage 並持久化 Session 於 Firestore。

## 📁 專案結構

```text
/
├── src/                # 原始碼目錄
│   ├── main.py         # FastAPI 後端主程式 (主入口)
│   └── sync_manager.py # Firebase 檔案同步管理工具
├── config/             # 設定檔目錄
│   └── firebase/       # Firebase 相關設定 (rules, service-account.json)
├── docs/               # 專案文件 (部署指南、開發計畫等)
├── tests/              # 測試與除錯腳本
├── archive/            # 暫存與封存檔案
├── templates/          # 前端 HTML 範本
├── requirements.txt    # Python 套件依賴清單
├── Dockerfile          # Docker 映像檔設定
├── firebase.json       # Firebase Hosting 設定
└── .env                # 本地環境變數 (不應上傳)
```

## 🚀 快速開始

### 1. 安裝套件
```bash
pip install -r requirements.txt
```

### 2. 設定憑證
在根目錄建立 `.env` 檔案，或在系統環境變數中設定：
```text
CULROC_USERNAME=您的帳號
CULROC_PASSWORD=您的密碼
```

### 3. 啟動伺服器
```bash
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```
訪問 `http://localhost:8000` 即可開始使用。

## 🛠️ 開發與同步工具

*   **Firebase 同步**：執行 `python src/sync_manager.py` 可將遠端網站檔案同步至您的 Firebase Storage。
*   **精準分類**：系統直接採用原始網站的分類路徑，避免關鍵字誤判。
*   **自動篩選**：同步時會自動比對雲端資料，僅列出「尚未同步」的新檔案，提升作業效率。
*   **測試腳本**：`tests/` 目錄下包含多種連線與解析測試工具。

## 📖 詳細文件

請參閱 `docs/` 目錄：
- [部署指南](docs/DEPLOY_GUIDE.md)
- [UI 開發計畫](docs/CLAUDE_UI_PLAN.md)

---

## 🛠️ 技術棧

*   **後端**: FastAPI (Python)
*   **資料庫**: Firebase Firestore
*   **儲存**: Firebase Storage
*   **前端**: Bootstrap 5 + Vanilla JS
*   **部署**: Docker / Hugging Face Spaces / Google Cloud Run
