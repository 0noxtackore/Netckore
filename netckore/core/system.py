"""System utilities shared by Netckore."""
import ctypes
import json
import os
import shutil
import sys


def project_root() -> str:
    """Return the absolute path of the project root."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(relative: str) -> str:
    """Resolve a resource path, working for source and PyInstaller bundles."""
    if getattr(sys, "_MEIPASS", None):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(project_root(), relative)


def frontend_path() -> str:
    """Path to the self-contained HTML/CSS/JS interface."""
    return resource_path(os.path.join("frontend", "index.html"))


def legacy_webview_data_path() -> str:
    """Path used by old Netckore versions (to be discarded)."""
    return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Netckore", "browser")


def load_config() -> dict:
    """Load user configuration from LOCALAPPDATA/Netckore/config.json."""
    folder = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Netckore")
    path = os.path.join(folder, "config.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def update_config(data: dict) -> None:
    """Merge ``data`` into the user configuration file."""
    folder = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Netckore")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "config.json")
    cfg = load_config()
    cfg.update(data)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def is_admin() -> bool:
    """True when the process runs with administrator rights (Windows)."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False