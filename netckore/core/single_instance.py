"""Single instance enforcement for Netckore (Windows only)."""
import os


def acquire():
    """Try to acquire the single-instance lock. Returns True on success."""
    if os.name != "nt":
        return True
    try:
        import win32event
        import win32api
        import pywintypes

        mutex_name = "Netckore.SingleInstance.Mutex"
        try:
            mutex = win32event.CreateMutex(None, False, mutex_name)
            last_error = win32api.GetLastError()
            return last_error != 183  # 183 = ERROR_ALREADY_EXISTS
        except pywintypes.error:
            return True
    except ImportError:
        # win32api not available; allow multiple instances
        return True


def focus_existing():
    """Bring the existing Netckore window to the front."""
    # Placeholder; could use Win32 to find and focus the existing window.
    pass