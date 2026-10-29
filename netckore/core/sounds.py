"""Native Windows sounds via MCI API (no pygame/SDL)."""
import os


class SoundPlayer:
    def __init__(self, resource_path_fn):
        self._resource_path = resource_path_fn
        self._enabled = os.name == "nt"

    def play(self, kind):
        if not self._enabled:
            return
        try:
            import ctypes
            # Simple system beep fallback; keep it light and dependency-free
            ctypes.windll.kernel32.Beep(
                {"success": 800, "danger": 400, "info": 600}.get(kind, 600),
                150,
            )
        except Exception:
            pass