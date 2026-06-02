# 檔案下載中心 - 前端 UI/UX 優化任務書

## 專案背景
本專案是一個內部的檔案下載系統。檔案已經由本地腳本同步至 **Firebase Storage**，其元數據（Metadata）存儲在 **Firestore**。
目前後端使用 FastAPI 提供一個 `/api/files` 接口，回傳 JSON 格式的檔案清單。

## 當前技術棧
- **後端**: FastAPI (Python)
- **前端**: 原生 HTML / Vanilla CSS / Vanilla JavaScript (Jinja2 模板)
- **資料庫**: Google Firestore

## API 資料結構 (`/api/files`)
回傳範例：
```json
{
  "files": [
    {
      "name": "115年青年創業貸款注意事項",
      "category": "行政",
      "download_url": "https://storage.googleapis.com/...",
      "size_mb": 2.5
    }
  ]
}
```

## 目前功能
1. 自動從 API 讀取清單。
2. 按類別（行政、財務、教育、督導、資訊、安全基金）分區顯示。
3. 具備關鍵字搜尋功能。
4. 具備類別下拉選單過濾。

## 需求：優化前端介面
請針對 `templates/index.html` 進行美化，目標是讓它看起來像是一個現代、專業的「企業級管理門戶」。

### 優化重點建議：
1. **視覺設計**:
   - 使用更現代的配色方案（例如深藍/淺灰或簡約白）。
   - 優化排版與間距（Whitespace）。
   - 增加檔案類別的標籤感（Tags）。
   - 為「下載」按鈕增加圖標（例如 FontAwesome 或內嵌 SVG）。

2. **交互體驗 (UX)**:
   - 增加滑鼠懸停效果（Hover effects）。
   - 增加加載動畫（Skeleton Screen 或更優雅的 Spinner）。
   - 當搜尋不到結果時，顯示更友善的提示。
   - 考慮行動裝置（RWD）的適配性。

3. **代碼結構**:
   - 保持單一 HTML 檔案結構（Vanilla JS），不引入大型框架（如 React/Vue）。
   - 優化 JavaScript 的渲染邏輯。

## 附件：目前的代碼 (`templates/index.html`)
[請將目前 templates/index.html 的內容貼在此處]
