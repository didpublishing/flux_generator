"""Quick test to verify ComfyUI connection"""
import urllib.request
import urllib.error
import sys

server = "127.0.0.1:8188"
endpoints = ["/system_stats", "/prompt", "/"]

print(f"Testing ComfyUI connection to {server}...")
print("=" * 50)

for endpoint in endpoints:
    try:
        url = f"http://{server}{endpoint}"
        req = urllib.request.Request(url)
        if endpoint == "/":
            req.get_method = lambda: "HEAD"
        urllib.request.urlopen(req, timeout=3)
        print(f"[OK] {endpoint} - ComfyUI is reachable!")
        sys.exit(0)
    except urllib.error.URLError as e:
        print(f"[ERROR] {endpoint} - URLError: {e}")
    except urllib.error.HTTPError as e:
        print(f"[WARNING] {endpoint} - HTTPError {e.code}: {e.reason}")
        if e.code == 405:  # Method not allowed is OK for HEAD
            print(f"   (This is OK - server is responding)")
            print(f"[OK] ComfyUI is reachable!")
            sys.exit(0)
    except Exception as e:
        print(f"[ERROR] {endpoint} - {type(e).__name__}: {e}")

print("\n[ERROR] All endpoints failed - ComfyUI may not be running")
sys.exit(1)

