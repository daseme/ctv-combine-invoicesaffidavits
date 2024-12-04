# build.py
import PyInstaller.__main__

PyInstaller.__main__.run([
    'main.py',
    '--name=Invoice_Merger',
    '--onefile',
    '--noconsole',
    '--add-data=resources;resources',
    '--icon=resources/icon.ico'
])