import requests
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

urls = [
    "http://www.culroc.org.tw/cu/",
    "https://www.culroc.org.tw/cu/"
]

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "python-requests/2.31.0",
    "" # Empty UA
]

def test_fetch(url, ua, headers=None):
    if headers is None:
        headers = {}
    headers["User-Agent"] = ua
    try:
        print(f"\nTesting URL: {url}")
        print(f"User-Agent: {ua}")
        print(f"Additional Headers: { {k:v for k,v in headers.items() if k != 'User-Agent'} }")
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"Status: {response.status_code}")
        print(f"Final URL: {response.url}")
    except Exception as e:
        print(f"Error: {e}")

for url in urls:
    for ua in user_agents:
        test_fetch(url, ua)

# Test with Referer
test_fetch("http://www.culroc.org.tw/cu/", user_agents[0], {"Referer": "http://www.google.com"})

# Test with Host header explicitly
test_fetch("http://www.culroc.org.tw/cu/", user_agents[0], {"Host": "www.culroc.org.tw"})
