import PyInstaller.__main__
import os

# Get absolute path to current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(BASE_DIR, 'ui')

# Check for icon
icon_path = os.path.join(BASE_DIR, 'icon.ico')
icon_option = f'--icon={icon_path}' if os.path.exists(icon_path) else None

args = [
    'main.py',
    '--name=AntigravityMouse',
    '--onefile',
    '--noconsole',
    f'--add-data={UI_DIR};ui',
    '--hidden-import=engineio.async_drivers.threading', 
    '--collect-all=mediapipe', # Force include all MediaPipe assets
    '--clean',
    # Exclude heavy unused modules
    '--exclude-module=tkinter',
    '--exclude-module=scipy',
    '--exclude-module=pandas',
]

if icon_option:
    args.append(icon_option)

PyInstaller.__main__.run(args)
