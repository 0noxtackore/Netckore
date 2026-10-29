"""Startup log for Netckore diagnostics."""
import os
import traceback
from datetime import datetime


_LOG_PATH = None
_DESKTOP_COPY = None


def _log_dir():
    return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Netckore")


def log_path():
    global _LOG_PATH
    if _LOG_PATH is None:
        folder = _log_dir()
        os.makedirs(folder, exist_ok=True)
        _LOG_PATH = os.path.join(folder, "netckore-startup.log")
    return _LOG_PATH


def log(message):
    path = log_path()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}\n"
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass


def log_exception(context):
    path = log_path()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {context}\n{traceback.format_exc()}\n")
    except OSError:
        pass


def export_desktop_copy():
    """Copy the startup log to the Desktop for the user to find."""
    src = log_path()
    if not os.path.exists(src):
        return src
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    dst = os.path.join(desktop, "Netckore-DIAGNOSTICO.txt")
    try:
        import shutil
        shutil.copy2(src, dst)
    except OSError:
        pass
    return dst