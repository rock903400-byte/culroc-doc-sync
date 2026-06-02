import json
import os
import re
import uuid
import requests
import firebase_admin
from firebase_admin import credentials, storage, firestore
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv

# 載入本地 .env 檔案
load_dotenv()

# Firebase 設定
SERVICE_ACCOUNT_FILE = "config/firebase/service-account.json"
STORAGE_BUCKET = "ceremonial-tea-397301.firebasestorage.app" # 使用您剛才確認的正確名稱

# 初始化 Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
    firebase_admin.initialize_app(cred, {
        'storageBucket': STORAGE_BUCKET
    })

db = firestore.client()
bucket = storage.bucket()

TARGET_BASE = "http://www.culroc.org.tw/cu/"
LOGIN_PAGE = TARGET_BASE
FILE_LIST_PAGE = TARGET_BASE + "?page_id=15"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Connection": "close",
}

# 排除 .rar 並過濾文件檔
_DOC_EXTENSIONS = re.compile(
    r"\.(pdf|docx?|xlsx?|pptx?|zip|7z|txt|csv|odt|ods|odp)(\?.*)?$",
    re.IGNORECASE,
)

MAX_FILE_SIZE_MB = 30  # 設定單個檔案上限為 30MB

def _sanitize_url(url: str) -> str:
    return url.replace("&#038;", "&").replace("&amp;", "&")

def _scrape_files(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    files = []
    seen = set()

    content_selectors = [".entry-content", ".page-content", "article", "main", "#content"]
    container = None
    for sel in content_selectors:
        container = soup.select_one(sel)
        if container: break
    
    search_root = container if container else soup
    for a in search_root.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "javascript:")): continue
        abs_url = urljoin(base_url, href)
        parsed = urlparse(abs_url)
        if not _DOC_EXTENSIONS.search(parsed.path) and "wpdmdl" not in href:
            continue
        if abs_url in seen: continue
        seen.add(abs_url)
        name = a.get_text(strip=True) or abs_url.split("/")[-1]
        files.append({"name": name, "url": abs_url, "type": "link"})

    adata_match = re.search(r"var aData\s*=\s*(\[\[.*?\]\]);", html, re.DOTALL)
    if adata_match:
        try:
            data = json.loads(adata_match.group(1))
            if len(data) > 1:
                for row in data[1:]:
                    if len(row) > 9:
                        fc, filename, cat1, cat2, display_name = row[6], row[1], row[2], row[3], row[7]
                        if not _DOC_EXTENSIONS.search(filename): continue
                        file_url = urljoin(base_url, f"/wp-content/uploads/webdownload/{fc}/{filename}")
                        if file_url not in seen:
                            seen.add(file_url)
                            files.append({
                                "name": display_name or filename,
                                "url": file_url,
                                "category": f"{cat1} / {cat2}",
                                "type": "file"
                            })
        except: pass
    return files

def parse_selection(selection_str, max_idx, files):
    indices = set()
    selection_str = selection_str.strip()
    if selection_str.lower() == 'all':
        return list(range(max_idx))
    available_groups = set(f['final_group'] for f in files)
    
    # 檢查是否為完整匹配或關鍵字匹配類別名稱
    matched_indices = []
    for group in available_groups:
        if selection_str == group or (selection_str and selection_str in group):
            matched_indices.extend([f['index'] for f in files if f['final_group'] == group])
    
    if matched_indices:
        return sorted(list(set(matched_indices)))
    parts = selection_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                indices.update(range(start, end + 1))
            except: pass
        else:
            try:
                indices.add(int(part))
            except: pass
    return [i for i in sorted(list(indices)) if 0 <= i < max_idx]

def _get_file_size(session, url):
    """取得遠端檔案大小 (MB)"""
    try:
        r = session.head(url, timeout=5, allow_redirects=True)
        size = int(r.headers.get('Content-Length', 0))
        if size == 0:
            # Fallback: 嘗試小規模 GET
            r = session.get(url, stream=True, timeout=5)
            size = int(r.headers.get('Content-Length', 0))
            r.close()
        return round(size / (1024 * 1024), 2)
    except:
        return 0

def main():
    username = os.getenv("CULROC_USERNAME")
    password = os.getenv("CULROC_PASSWORD")
    if not username or not password:
        print("錯誤: 請先在 .env 檔案中設定 CULROC_USERNAME 和 CULROC_PASSWORD")
        return

    session = requests.Session()
    session.headers.update(HEADERS)

    print(f"正在登入目標網站: {LOGIN_PAGE}...")
    try:
        r = session.get(LOGIN_PAGE, timeout=60)
        soup = BeautifulSoup(r.text, "lxml")
        payload = {}
        form = None
        for f in soup.find_all("form"):
            if "user_password" in str(f):
                form = f
                break
        
        if form:
            for inp in form.find_all("input"):
                n, v = inp.get("name"), inp.get("value", "")
                if n: payload[n] = v
            user_field = next((k for k in payload if k.startswith("username")), "username")
            pass_field = next((k for k in payload if k.startswith("user_password")), "user_password")
            payload[user_field] = username
            payload[pass_field] = password
            action_url = urljoin(r.url, _sanitize_url(form.get("action", r.url)))
            session.post(action_url, data=payload, timeout=60)

        print(f"正在抓取檔案清單...")
        r_list = session.get(FILE_LIST_PAGE, timeout=60)
        files = _scrape_files(r_list.text, FILE_LIST_PAGE)

        if not files:
            print("找不到任何檔案。")
            return

        print("正在比對雲端已同步的檔案...")
        existing_docs = db.collection("my_files").stream()
        synced_urls = {doc.to_dict().get("original_url") for doc in existing_docs if doc.to_dict().get("original_url")}
        
        unsynced_files = [f for f in files if f['url'] not in synced_urls]
        
        print(f"網站上共有 {len(files)} 個檔案，其中 {len(unsynced_files)} 個尚未同步。")
        
        if not unsynced_files:
            print("所有檔案都已經同步過了！目前沒有需要更新的檔案。")
            return
            
        files = unsynced_files

        print("\n正在讀取檔案大小資訊，請稍候...")
        grouped_files = {}
        for i, f in enumerate(files):
            group = f.get('category', '未分類')
            f['index'] = i
            f['final_group'] = group
            # 預先抓取大小
            f['size_mb'] = _get_file_size(session, f['url'])
            if group not in grouped_files:
                grouped_files[group] = []
            grouped_files[group].append(f)

        print("\n--- 檔案清單 (已自動排除 .rar) ---")
        for group, items in grouped_files.items():
            if items:
                print(f"\n【{group}】")
                for f in items: 
                    size_text = f"{f['size_mb']}MB" if f['size_mb'] > 0 else "未知大小"
                    print(f"  [{f['index']}] {f['name']} ({size_text})")
        
        print("\n------------------")
        print(f"注意：將自動跳過超過 {MAX_FILE_SIZE_MB}MB 的大型檔案。")
        selection = input("請輸入要同步的編號 (例如 1,3,5-8) 或直接輸入類別名稱 (例如: 督導) 或 all: ")
        selected_indices = parse_selection(selection, len(files), files)

        if not selected_indices:
            print("未選擇任何有效檔案。")
            return

        print(f"\n準備同步 {len(selected_indices)} 個檔案...")
        
        for idx in selected_indices:
            f = files[idx]
            
            # 使用已抓取的大小
            size_mb = f['size_mb']
            if size_mb > MAX_FILE_SIZE_MB:
                print(f"\n[{idx}] 跳過: {f['name']} (檔案過大: {size_mb}MB)")
                continue

            print(f"\n[{idx}] 處理中: {f['name']} ({size_mb if size_mb > 0 else '未知'}MB)")
            
            try:
                # 1. 下載檔案
                print("   下載中...")
                fr = session.get(f['url'], timeout=60, stream=True)
                fr.raise_for_status()
                
                ext = ""
                if "." in f['url'].split("/")[-1]:
                    ext = "." + f['url'].split("/")[-1].split(".")[-1].split("?")[0]
                
                temp_filename = f"temp_{idx}{ext}"
                with open(temp_filename, "wb") as tmp:
                    for chunk in fr.iter_content(chunk_size=8192):
                        tmp.write(chunk)
                
                # 2. 上傳到 Firebase Storage
                print("   上傳到 Firebase Storage...")
                blob_path = f"files/{f['final_group']}/{f['name']}{ext}"
                blob = bucket.blob(blob_path)
                blob.upload_from_filename(temp_filename)
                blob.make_public()
                new_url = blob.public_url
                
                # 3. 儲存資訊到 Firestore
                print("   紀錄到資料庫...")
                safe_group = re.sub(r'[.#$/\[\]]', '_', f['final_group'])
                safe_name = re.sub(r'[.#$/\[\]]', '_', f['name'])
                doc_id = f"{safe_group}_{safe_name}"
                
                db.collection("my_files").document(doc_id).set({
                    "name": f['name'],
                    "category": f['final_group'],
                    "original_url": f['url'],
                    "download_url": new_url,
                    "sync_at": firestore.SERVER_TIMESTAMP,
                    "size_mb": size_mb
                })
                
                os.remove(temp_filename)
                print("   完成！")
                
            except Exception as e:
                print(f"   失敗: {e}")

        print("\n所有選中的檔案已同步完成！")

    except Exception as e:
        print(f"執行出錯: {e}")

if __name__ == "__main__":
    main()
