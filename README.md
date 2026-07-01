# director

> 理事管理後台 — 行動裝置友善之文件下載代理系統

## 功能特色

- **動態檔案爬取**：解析 CULROC 網站的動態 JS `aData` 資料下載檔案。
- **免密一鍵登入**：後端預設憑證登入，使用者無需輸入帳密。
- **行動優化**：基於 Bootstrap 5 的行動裝置優化代理下載。
- **Firebase 備份**：支援同步備份至 Firebase Storage。

## 技術棧

- **Frontend**: HTML, CSS (Bootstrap 5)
- **Backend**: FastAPI (Python)

## 快速開始

### 啟動後端代理服務
```bash
pip install -r requirements.txt
python -m uvicorn src.main:app --reload
```

## 專案結構

```text
/
├── src/main.py         # FastAPI 核心與下載代理邏輯
└── templates/          # 前端 HTML 模板
```

## License

MIT
