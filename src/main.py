import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin, urlparse

import firebase_admin
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Query
from firebase_admin import credentials, firestore, storage

# Load environment variables from .env file
load_dotenv()
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

TARGET_BASE = "https://www.culroc.org.tw/cu/"
LOGIN_PAGE = TARGET_BASE
FILE_LIST_PAGE = TARGET_BASE + "?page_id=15"

app = FastAPI()
templates = Jinja2Templates(directory="templates")

STORAGE_BUCKET = "ceremonial-tea-397301.firebasestorage.app"

_SA_FILE = "config/firebase/service-account.json"

if not firebase_admin._apps:
    try:
        if os.path.exists(_SA_FILE):
            firebase_admin.initialize_app(credentials.Certificate(_SA_FILE), {"storageBucket": STORAGE_BUCKET})
        else:
            firebase_admin.initialize_app(options={"storageBucket": STORAGE_BUCKET})
    except Exception as e:
        print(f"Firebase Init Warning: {e}")

try:
    db = firestore.client()
except Exception as e:
    print(f"Firestore Client Error: {e}")
    db = None # 防止啟動失敗，改在執行時報錯

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Connection": "close",  # Avoid keep-alive issues with some servers
}


def _sanitize_url(url: str) -> str:
    """Sanitize URL by replacing HTML entities often found in WordPress redirects."""
    return url.replace("&#038;", "&").replace("&amp;", "&")


def _make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def _get_session_from_db(session_id: str) -> Optional[requests.Session]:
    if db is None:
        return None
    doc_ref = db.collection("sessions").document(session_id)
    doc = doc_ref.get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    sess = _make_session()
    sess.cookies.update(data.get("cookies", {}))
    return sess


def _save_session_to_db(session_id: str, sess: requests.Session):
    if db is None:
        print("Error: Firestore DB is not initialized")
        return
    doc_ref = db.collection("sessions").document(session_id)
    doc_ref.set({
        "cookies": sess.cookies.get_dict(),
        "last_active": firestore.SERVER_TIMESTAMP
    })


_CONTENT_SELECTORS = [
    ".entry-content",
    ".page-content",
    ".post-content",
    ".content-area",
    "article",
    "main",
    "#content",
    ".site-content",
]

_FILE_EXTENSIONS = re.compile(
    r"\.(pdf|docx?|xlsx?|pptx?|zip|rar|7z|txt|csv|odt|ods|odp)(\?.*)?$",
    re.IGNORECASE,
)

_WP_DOWNLOAD_PARAMS = re.compile(
    r"[?&](wpdmdl|download_id|dl_id|attachment_id|did|fid)=\d+",
    re.IGNORECASE,
)


def _scrape_files(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    files = []
    seen = set()

    # 1. Static Links
    # Find the main content container to avoid nav/footer/sidebar links
    container = None
    for sel in _CONTENT_SELECTORS:
        container = soup.select_one(sel)
        if container:
            break

    search_root = container if container else soup

    for a in search_root.find_all("a", href=True):
        href: str = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "javascript:")):
            continue

        abs_url = urljoin(base_url, href)
        parsed = urlparse(abs_url)

        if container:
            # Inside a known content area: accept all http/https links
            if parsed.scheme not in ("http", "https"):
                continue
        else:
            # No content area found: fall back to strict pattern matching
            is_file = _FILE_EXTENSIONS.search(parsed.path)
            is_upload = "wp-content/uploads" in abs_url
            is_download_flag = "download" in href.lower() or "file" in href.lower()
            is_wp_download = bool(_WP_DOWNLOAD_PARAMS.search(href))
            if not (is_file or is_upload or is_download_flag or is_wp_download):
                continue

        if abs_url in seen:
            continue
        seen.add(abs_url)

        name = a.get_text(strip=True) or parsed.path.split("/")[-1] or abs_url
        files.append({"name": name, "url": abs_url})

    # 2. Dynamic Links (aData array in script)
    # The site uses a JS variable aData to store file info and generates links on the fly.
    adata_match = re.search(r"var aData\s*=\s*(\[\[.*?\]\]);", html, re.DOTALL)
    if adata_match:
        try:
            raw_data = adata_match.group(1)
            data = json.loads(raw_data)
            # data structure: [header, [id, filename, cat1, cat2, ext, user, fc, display_name, remark, date], ...]
            # Link construction: /wp-content/uploads/webdownload/{fc}/{filename}
            if len(data) > 1:
                for row in data[1:]:
                    if len(row) > 9:
                        fc = row[6]
                        filename = row[1]
                        cat1 = row[2]
                        cat2 = row[3]
                        display_name = row[7]
                        remark = row[8]
                        date = row[9]
                        
                        file_url = urljoin(base_url, f"/wp-content/uploads/webdownload/{fc}/{filename}")
                        if file_url not in seen:
                            seen.add(file_url)
                            files.append({
                                "name": display_name or filename,
                                "url": file_url,
                                "category": f"{cat1} / {cat2}",
                                "date": date,
                                "remark": remark
                            })
        except Exception:
            pass  # Fail gracefully if JS parsing fails

    return files


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 記憶體快取設計 (TTL: 300秒 / 5分鐘)
class SimpleCache:
    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self.data = None
        self.expire_at = 0

    def get(self):
        if self.data is not None and time.time() < self.expire_at:
            return self.data
        return None

    def set(self, data):
        self.data = data
        self.expire_at = time.time() + self.ttl

files_cache = SimpleCache(ttl=300)


@app.get("/api/files")
async def get_files():
    if db is None:
        raise HTTPException(status_code=500, detail="資料庫未初始化")
    
    # 嘗試從快取中取得資料
    cached_files = files_cache.get()
    if cached_files is not None:
        return {"files": cached_files}
    
    try:
        # 從 Firestore 讀取所有已同步的檔案
        docs = db.collection("my_files").order_by("sync_at", direction=firestore.Query.DESCENDING).stream()
        
        files = []
        for doc in docs:
            data = doc.to_dict()
            files.append({
                "name": data.get("name"),
                "category": data.get("category"),
                "download_url": data.get("download_url")
            })
            
        # 寫入快取
        files_cache.set(files)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取資料庫失敗: {e}")
