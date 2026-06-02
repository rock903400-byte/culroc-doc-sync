# Project Specification: Mobile-Friendly Web Downloader Agent

## Overview
This project is a Web Application that allows users to login to a specific website (`http://www.culroc.org.tw/cu/?page_id=15`) via a mobile-friendly interface, view a list of downloadable files, and download selected files.

The application uses a Backend-as-a-Proxy architecture to handle authentication and scraping, bypassing CORS and mobile browser limitations.

## Tech Stack
- **Backend**: Python (FastAPI)
- **Frontend**: HTML5, CSS3 (Bootstrap 5 for RWD), JavaScript (Vanilla)
- **Libraries**:
    - `fastapi`, `uvicorn` (Web Server)
    - `requests` (HTTP Client with Session support)
    - `beautifulsoup4` (HTML Scraping)
    - `python-multipart` (For form data handling)

## Project Structure
```
/
├── main.py              # FastAPI Backend
├── templates/
│   └── index.html       # Single Page Application (Login + List)
├── requirements.txt     # Python Dependencies
└── README.md            # Execution Instructions
```

## Detailed Requirements

### 1. Backend (`main.py`)
- **Login Proxy (`POST /api/login`)**:
    - Accept `username` and `password`.
    - Use `requests.Session()` to POST to the target site.
    - Note: The target site is a WordPress site using the `Ultimate Member` plugin. Need to handle `_wpnonce` and other hidden fields if present.
    - After successful login, navigate to `http://www.culroc.org.tw/cu/?page_id=15`.
    - Scrape the page for all file download links.
    - Return a JSON list of files: `[{"name": "Filename", "url": "Absolute URL"}, ...]`.
    - Store the `Session` (e.g., in a global dict or use a session cookie) to maintain the login state for downloads.

- **Download Proxy (`GET /api/download`)**:
    - Accept a `url` parameter.
    - Use the stored session to fetch the file content.
    - Stream the file back to the user with appropriate `Content-Disposition` headers.

- **Static Files**:
    - Serve `index.html` at the root `/`.

### 2. Frontend (`index.html`)
- **Design**: 
    - Use Bootstrap 5 for a mobile-first UI.
    - Simple login form (Username/Password).
    - "Loading" spinner during API calls.
    - Scrollable list of files with large, touch-friendly "Download" buttons.
- **Logic**:
    - Use `fetch()` to interact with the API.
    - Switch between "Login View" and "List View" without page refresh.

### 3. Security & Constraints
- Do not store user credentials on the server.
- Proxy all requests to avoid CORS issues on the phone.

## Target Site Info
- **URL**: `http://www.culroc.org.tw/cu/?page_id=15`
- **Login Form Details**:
    - Form ID: `2004` (Based on initial scrape)
    - Fields: `username-2004`, `user_password-2004`, `form_id`, `_wpnonce`.

---

**Instructions for Claude Code**:
Please implement the above specification. Focus on making the Python backend robust (handling session timeouts and login failures) and the HTML frontend very clean and usable on a small mobile screen.
