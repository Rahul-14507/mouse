import webview
import os
import threading
import sys
from core.controller import MouseController

class Api:
    def __init__(self):
        self.controller = MouseController()

    def start_mouse(self):
        self.controller.start()
        return "Started"

    def stop_mouse(self):
        self.controller.stop()
        return "Stopped"

    def update_config(self, key, value):
        self.controller.update_config(key, value)
        return f"Updated {key}"
        
    def get_config(self):
        return self.controller.config

    def check_updates(self):
        from utils.updater import check_for_updates, open_download_page
        result = check_for_updates()
        return result

    def open_url(self, url):
        import webbrowser
        webbrowser.open(url)

def on_closed():
    api.controller.stop()
    sys.exit()

window = None

def stop_callback():
    # Called from controller when Fist is detected
    if window:
        window.evaluate_js("window.dispatchEvent(new Event('stop_mouse_event'))")

if __name__ == '__main__':
    api = Api()
    
    # Pass callback to controller
    api.controller.set_stop_callback(stop_callback)
    
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui', 'index.html')
    
    window = webview.create_window(
        'Antigravity Mouse', 
        url=ui_path,
        width=400,
        height=600,
        resizable=False,
        background_color='#0f0f13',
        js_api=api
    )
    
    webview.start(debug=False)
