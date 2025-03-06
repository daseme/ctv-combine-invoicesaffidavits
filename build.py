import os
os.environ["PYINSTALLER_DISABLE_SET_EXE_BUILD_TIMESTAMP"] = "1"
os.environ["PYINSTALLER_DISABLE_EXE_CHECKSUM"] = "1"

import PyInstaller.__main__

PyInstaller.__main__.run([
    '--name=Invoice_Merger',
    '--onefile',
    '--noconsole',
    'main.py'
])
