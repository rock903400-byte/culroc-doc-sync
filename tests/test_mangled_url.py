import requests

# The literal Location header from the server
mangled_url = "http://www.culroc.org.tw/cu/?page_id=5&#038;redirect_to=http%3A%2F%2Fwww.culroc.org.tw%2Fcu%2F"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

try:
    print(f"Testing mangled URL: {mangled_url}")
    response = requests.get(mangled_url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Final URL: {response.url}")
except Exception as e:
    print(f"Error: {e}")
