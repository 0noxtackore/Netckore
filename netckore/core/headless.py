"""Headless elevated worker for Netckore (placeholder for future admin actions)."""
import os
import sys


DONE = "#done"
SUMMARY = "#summary"
LOG_KINDS = {"info", "warning", "error", "success"}


def log_path():
    """Path to the elevated run log file."""
    return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Netckore", "headless.log")


def launch_elevated(selected, lang):
    """Launch an elevated copy of Netckore for actions requiring admin rights.

    Placeholder: no admin-only actions exist yet in Netckore v0.1.0.
    """
    # Netckore v0.1.0 runs entirely unprivileged; admin actions may be added later.
    return True