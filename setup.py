import sys
from cx_Freeze import setup, Executable

# Define build options
build_exe_options = {
    "packages": [
        "os", "re", "logging", "json", "time", "queue",
        "threading", "datetime", "PyPDF2", "ttkbootstrap", "tkinter"
    ],
    "excludes": [],
}

# On Windows, use "Win32GUI" to hide the console.
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Invoice_Merger",
    version="1.0",
    description="Invoice and Affidavit Merger",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base)]
)
