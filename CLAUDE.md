# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# 啟動開發伺服器
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 手動同步 culroc.org.tw 的檔案至 Firebase Storage（互動式 CLI）
python src/sync_manager.py
```

## Architecture

這是一個**信合社文件下載中心**，讓使用者瀏覽並下載信合社相關文件。

### 資料流

```
culroc.org.tw（來源網站）
    ↓ sync_manager.py（爬蟲 + 互動式選擇）
Firebase Storage（公開檔案儲存）
    ↓ Firestore my_files collection（metadata）
GET /api/files
    ↓
index.html（前端 JS 渲染）
```

### 兩個進入點

- **`src/main.py`**：FastAPI 應用，只有兩個 route：`GET /`（回傳 HTML）和 `GET /api/files`（從 Firestore 讀 metadata）。Firebase 初始化時，本機自動使用 `config/firebase/service-account.json`，Cloud Run 則走 ADC。
- **`src/sync_manager.py`**：獨立 CLI 工具，登入 culroc.org.tw、爬取檔案清單、互動式選擇要同步哪些，下載後上傳至 Firebase Storage 並寫入 Firestore。

### Firebase

- **Project ID**：`ceremonial-tea-397301`
- **Storage bucket**：`ceremonial-tea-397301.firebasestorage.app`
- **Firestore collection**：`my_files`，欄位為 `name`, `category`, `download_url`, `sync_at`, `size_mb`
- **本機憑證**：`config/firebase/service-account.json`（已加入 `.gitignore`）

### 前端

`templates/index.html` 是單一 HTML 檔，無框架，純 Vanilla JS。頁面載入後呼叫 `/api/files`，在前端做搜尋與類別過濾，不會再打 API。

### 新增檔案的方式

不透過 Web UI，直接請 Claude Code 執行 Python 腳本上傳至 Firebase Storage，並寫入 Firestore。
