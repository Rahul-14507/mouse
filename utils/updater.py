import json
import urllib.request
import webbrowser

CURRENT_VERSION = "1.0.0"
# Replace with your actual repo URL when ready
VERSION_URL = "https://raw.githubusercontent.com/Rahul-14507/mouse/main/version.json" 

def check_for_updates():
    try:
        with urllib.request.urlopen(VERSION_URL) as response:
            data = json.loads(response.read().decode())
            latest_version = data.get("version")
            download_url = data.get("download_url")
            
            if latest_version and latest_version != CURRENT_VERSION:
                return {
                    "update_available": True,
                    "latest_version": latest_version,
                    "download_url": download_url
                }
    except Exception as e:
        print(f"Update check failed: {e}")
    
    return {"update_available": False}

def open_download_page(url):
    webbrowser.open(url)
