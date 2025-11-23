import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "frame_margin": 70,
    "smoothening_fast": 3,
    "smoothening_medium": 6,
    "smoothening_slow": 10,
    "click_threshold": 30,
    "stabilize_threshold": 50,
    "drag_threshold": 30,
    "scroll_threshold": 15,
    "scroll_enabled": True,
    "right_click_enabled": True,
    "camera_feed_enabled": False,
    "enabled": False # Start disabled by default
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Merge with default to ensure all keys exist
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
    except:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")
