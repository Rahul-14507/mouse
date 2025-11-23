import PyInstaller.__main__
import os

# Get absolute path to current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(BASE_DIR, 'ui')

PyInstaller.__main__.run([
    'main.py',
    '--name=AntigravityMouse',
    '--onefile',
    '--noconsole',
    f'--add-data={UI_DIR};ui', # Include UI folder
    '--hidden-import=engineio.async_drivers.threading', # Fix for python-socketio/engineio if needed
    '--clean'
])
