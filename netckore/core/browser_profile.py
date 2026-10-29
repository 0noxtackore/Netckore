"""WebView2 profile management for Netckore."""
import os
import shutil


def kill_stale_processes():
    """Kill leftover WebView2 processes from previous runs."""
    killed = 0
    if os.name != "nt":
        return killed
    try:
        import subprocess
        result = subprocess.run(
            ["taskkill", "/F", "/IM", "msedgewebview2.exe", "/T"],
            capture_output=True, text=True, timeout=10,
        )
        killed = 1 if result.returncode == 0 else 0
    except Exception:
        pass
    return killed


def new_profile():
    """Create a fresh private WebView2 profile for this run."""
    if os.name != "nt":
        return None
    base = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Netckore", "browser")
    profile = os.path.join(base, f"profile-{os.getpid()}")
    try:
        os.makedirs(profile, exist_ok=True)
        return profile
    except OSError:
        return None


def remove_old_profiles(current_profile):
    """Remove old profiles except the current one."""
    removed = 0
    if os.name != "nt":
        return removed
    base = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Netckore", "browser")
    if not os.path.isdir(base):
        return removed
    for name in os.listdir(base):
        path = os.path.join(base, name)
        if path == current_profile:
            continue
        if os.path.isdir(path) and name.startswith("profile-"):
            try:
                shutil.rmtree(path)
                removed += 1
            except OSError:
                pass
    return removed