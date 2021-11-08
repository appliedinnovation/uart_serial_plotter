import os
import sys

try:
    base_path = sys._MEIPASS
    print("[RESOURCE] Running as a package")
except Exception:
    print("[RESOURCE] Running from source")


def path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath("./")

    print("[RESOURCE]", relative_path)
    rPath = os.path.join(base_path, relative_path)
    return rPath


def open(path):
    command = ""
    if sys.platform.startswith("win"):
        command = ""
        path = '"' + path + '"'
    elif sys.platform.startswith("linux") or sys.platform.startswith("cygwin"):
        command = "open "
    elif sys.platform.startswith("darwin"):
        command = "open "
    else:
        raise EnvironmentError("Unsupported platform")

    os.system(command + path)
