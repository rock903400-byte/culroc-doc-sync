import requests

url = "http://www.culroc.org.tw/cu/"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Connection": "close"
}

print("Testing with Connection: close")
try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Final URL: {response.url}")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting without following redirects automatically")
try:
    response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
    print(f"Status: {response.status_code}")
    print(f"Location: {response.headers.get('Location')}")
    
    if response.status_code == 302:
        loc = response.headers.get('Location')
        # Fix the &#038; if present
        loc = loc.replace('&#038;', '&')
        print(f"Following manually to: {loc}")
        response2 = requests.get(loc, headers=headers, timeout=10)
        print(f"Status 2: {response2.status_code}")
except Exception as e:
    print(f"Error: {e}")
