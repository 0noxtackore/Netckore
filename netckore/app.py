"""Netckore backend: HTML/CSS interface (pywebview) + network diagnosis runner.

The Python side keeps every diagnosis/monitoring/i18n function; the presentation
layer is a self-contained HTML/CSS/JS interface rendered by pywebview
(Edge WebView2 on Windows 10/11).
"""
import inspect
import json
import os
import sys
import threading
import time  # Added for the pusher loop

from datetime import datetime

try:
    import webview
except ImportError as exc:
    raise SystemExit(
        f"Missing dependency: {exc.name}\n"
        "Install the requirements with: pip install -r requirements.txt"
    )

from . import __version__
from .core import (
    browser_profile,
    headless,
    monitoring,
    single_instance,
    startup_log,
)
from .core.system import (
    frontend_path,
    is_admin,
    legacy_webview_data_path,
    load_config,
    project_root,
    resource_path,
    update_config,
)
from .i18n import LANGUAGE_OPTIONS, TranslationManager, _

# Languages shown first in the selector.
_LANG_PRIORITY = ["es", "en", "fr", "de", "pt", "it", "ru", "ja", "zh", "ko", "ar"]


def _saved_categories():
    """Diagnosis categories the user picked last time (empty when none/invalid)."""
    saved = load_config().get("categories")
    if not isinstance(saved, list):
        return []
    known = {c["id"] for c in monitoring.diagnosis_categories()}
    return [c for c in saved if isinstance(c, str) and c in known]


class Api:
    """API exposed to the JavaScript frontend as ``window.pywebview.api``.

    Same rules as Fluxckore: only methods may be public. Every non-method
    attribute must be private (leading underscore) so pywebview does not recurse
    into a half-built .NET object graph from a worker thread.
    """

    def __init__(self):
        self._window = None
        self._is_diagnosing = False
        self._log_queue = []
        self._events = []
        self._lock = threading.Lock()

        # Startup handshake: the page calls ``frontend_ready`` after its first
        # paint, so the backend knows WebView2 really started rendering.
        self._ready = threading.Event()
        self._js_pending = False
        self._push_errors = 0

    # ------------------------------------------------------------------
    # Called from JavaScript
    # ------------------------------------------------------------------
    def frontend_ready(self):
        """Called by the UI after its first paint (startup diagnostics)."""
        startup_log.log("frontend: ready reported by the page")
        self._ready.set()
        return {"ok": True}

    def get_init_data(self):
        """Initial payload: version, language options and translations."""
        lang = TranslationManager.get_current_language()
        available = TranslationManager.get_available_languages()

        options = []
        for code, data in LANGUAGE_OPTIONS.items():
            if code in available:
                options.append({"code": code, "native": data["native"]})
        options.sort(
            key=lambda o: _LANG_PRIORITY.index(o["code"])
            if o["code"] in _LANG_PRIORITY
            else len(_LANG_PRIORITY)
        )

        return {
            "version": __version__,
            "lang": lang,
            "lang_options": options,
            "translations": TranslationManager.get_translations(),
            "categories": monitoring.diagnosis_categories(),
            "selected": _saved_categories(),
        }

    def set_language(self, code):
        """Switch UI language and return the new translations."""
        if TranslationManager.set_language(code):
            print(f"[i18n] Language changed to: {code}")
            update_config({"language": code})
            return {"ok": True, "lang": code, "translations": TranslationManager.get_translations()}
        return {"ok": False}

    def set_categories(self, categories=None):
        """Persist the diagnosis categories chosen by the user."""
        known = {c["id"] for c in monitoring.diagnosis_categories()}
        if not isinstance(categories, (list, tuple)):
            return {"ok": False}
        selected = [c for c in categories if isinstance(c, str) and c in known]
        update_config({"categories": selected})
        return {"ok": True}

    def start_diagnosis(self, categories=None):
        """Start a network diagnosis run in a worker thread."""
        if self._is_diagnosing:
            return {"ok": False}

        known = {c["id"] for c in monitoring.diagnosis_categories()}
        if not isinstance(categories, (list, tuple)) or not categories:
            selected = monitoring.default_categories()
        else:
            selected = [c for c in categories if isinstance(c, str) and c in known]
        if not selected:
            return {"ok": False}

        self._is_diagnosing = True
        threading.Thread(target=self._run_diagnosis, args=(selected,), daemon=True).start()
        return {"ok": True}

    # ------------------------------------------------------------------
    # Backend -> frontend
    # ------------------------------------------------------------------
    def _log(self, message, message_type="info"):
        """Queue a log entry for the frontend."""
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "message": message,
            "type": message_type,
        }
        with self._lock:
            self._log_queue.append(entry)

    def _emit(self, event):
        """Queue a UI event (summary dialog, run finished...)."""
        with self._lock:
            self._events.append(event)

    def _pusher(self):
        """Periodic loop: system stats + queued logs/events -> frontend."""
        startup_log.log("pusher: thread started")

        if not self._ready.wait(15):
            startup_log.log("pusher: page not ready after 15 s, pushing anyway")

        while True:
            time.sleep(1)
            try:
                with self._lock:
                    logs, self._log_queue = self._log_queue, []
                    events, self._events = self._events, []

                # New: collect live network stats from monitoring
                try:
                    stats = monitoring.collect_network_stats()
                except Exception:
                    stats = {"online": False, "timestamp": datetime.now().strftime("%H:%M:%S")}

                payload = {
                    "stats": stats,
                    "logs": logs,
                    "events": events,
                }

                self._push_js(f"window.UI && UI.onData({json.dumps(payload)})")
            except Exception:
                if self._push_errors < 3:
                    self._push_errors += 1
                    startup_log.log_exception("pusher: tick failed")

    def _push_js(self, script):
        """Send a script to the page without ever blocking the stats loop."""
        if self._js_pending:
            return
        self._js_pending = True

        def run():
            try:
                if self._window is not None:
                    self._window.evaluate_js(script)
            except Exception:
                if self._push_errors < 3:
                    self._push_errors += 1
                    startup_log.log_exception("pusher: evaluate_js failed")
            finally:
                self._js_pending = False

        threading.Thread(target=run, daemon=True).start()

    # ------------------------------------------------------------------
    # Diagnosis run (same structure as before, using monitoring.run_diagnosis)
    # ------------------------------------------------------------------
    def _report_summary(self, results):
        """Log + announce the totals of a finished diagnosis run."""
        self._log("════════════════════════════════════════", "info")
        self._log(f"     {_('diagnosis_summary')}     ", "success")
        self._log("═══════════════════════════════════════", "info")

        online = results.get("online", False)
        status = _("connection_online") if online else _("connection_offline")
        self._log(f"[ESTADO] {status}", "success" if online else "warning")

        ping = results.get("ping_avg")
        if ping is not None:
            self._log(f"[PING] {ping} ms", "info")

        for step in results.get("steps", []):
            kind = step.get("kind", "info")
            self._log(step.get("message", ""), kind)

        self._emit({"kind": "summary", "results": results})
        self._is_diagnosing = False

    def _run_diagnosis(self, selected):
        try:
            log = self._log

            self._log("════════════════════════════════════════", "info")
            self._log(f"     {_('starting_diagnosis')}     ", "success")
            self._log("════════════════════════════════════════", "info")

            results = monitoring.run_diagnosis(selected, log)
            self._report_summary(results)
        except Exception as e:
            self._log(f"Critical error: {e}", "error")
        finally:
            self._emit({"kind": "done"})


def _load_html() -> str:
    """Read the self-contained HTML/CSS/JS interface."""
    path = frontend_path()
    if not os.path.exists(path):
        raise FileNotFoundError(f"Interface not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _set_app_user_model_id() -> None:
    """Give the process its own AppUserModelID."""
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Netckore.App"
        )
    except Exception:
        pass


def window_icon_path() -> str:
    """Icon shown in the window/taskbar (generated from the app logo)."""
    return resource_path(os.path.join("frontend", "icon.ico"))


def _webview2_available() -> bool:
    """True when the Edge WebView2 runtime is installed on this machine."""
    if os.environ.get("NETCKORE_SKIP_WEBVIEW_CHECK") == "1":
        return True
    try:
        import winreg
    except Exception:
        return True

    guid = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    keys = (
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\\" + guid),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\EdgeUpdate\Clients\\" + guid),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\EdgeUpdate\Clients\\" + guid),
    )
    for root, subkey in keys:
        try:
            with winreg.OpenKey(root, subkey) as handle:
                version, _ = winreg.QueryValueEx(handle, "pv")
            if version and version != "0.0.0.0":
                return True
        except OSError:
            continue

    for base in (
        os.environ.get("ProgramFiles(x86)"),
        os.environ.get("ProgramFiles"),
    ):
        if not base:
            continue
        application = os.path.join(base, "Microsoft", "EdgeWebView", "Application")
        try:
            for name in os.listdir(application):
                if os.path.exists(os.path.join(application, name, "msedgewebview2.exe")):
                    return True
        except OSError:
            continue
    return False


def _show_message(text: str, title: str = "Netckore") -> None:
    """Show a native message box (the frozen build has no console)."""
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, text, title, 0x00000030)
    except Exception:
        pass


def _export_diagnostics() -> str:
    """Copy the startup log to the Desktop with a name users can find."""
    return startup_log.export_desktop_copy()


def _discard_legacy_profile() -> None:
    """Delete the WebView2 folder used by a previous run, once, in the background."""
    import shutil

    path = legacy_webview_data_path()
    if not os.path.isdir(path):
        return
    try:
        shutil.rmtree(path)
        startup_log.log("legacy WebView2 profile removed")
    except OSError:
        startup_log.log("legacy WebView2 profile could not be removed (in use)")


def _redirect_stderr_to_log() -> None:
    """Send stderr to a log file for the rest of the session."""
    if not getattr(sys, "stderr", None):
        return
    try:
        folder = os.path.dirname(startup_log.log_path())
        log_path = os.path.join(folder, "netckore.log")
        fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
        os.dup2(fd, 2)
        os.close(fd)
    except Exception:
        pass


def main():
    """Entry point: elevation, language setup, window launch."""
    startup_log.log(f"=== Netckore {__version__} ===")
    startup_log.log(
        f"env: frozen={bool(getattr(sys, 'frozen', False))} "
        f"exe={sys.executable} cwd={os.getcwd()}"
    )
    try:
        from importlib.metadata import version as _package_version

        try:
            webview_version = _package_version("pywebview")
        except Exception:
            webview_version = getattr(webview, "__version__", "?")
        startup_log.log(
            f"python={sys.version.split()[0]} webview={webview_version}"
        )
    except Exception:
        pass

    _redirect_stderr_to_log()
    startup_log.log("stderr redirected")

    _set_app_user_model_id()

    if not single_instance.acquire():
        startup_log.log("another Netckore instance is already running: focusing it")
        single_instance.focus_existing()
        return

    startup_log.log(f"administrator={is_admin()}")

    killed = browser_profile.kill_stale_processes()
    startup_log.log(f"stale WebView2 processes killed={killed}")
    profile_path = browser_profile.new_profile()
    startup_log.log(f"WebView2 profile: {profile_path}")
    if profile_path:
        removed = browser_profile.remove_old_profiles(profile_path)
        startup_log.log(f"old WebView2 profiles removed={removed}")

    if not _webview2_available():
        startup_log.log("WebView2 runtime NOT found: aborting with a clear message")
        _show_message(
            "Netckore necesita el componente 'Microsoft Edge WebView2' y este "
            "equipo no lo tiene instalado.\n\n"
            "Instálalo gratis desde:\n"
            "https://developer.microsoft.com/microsoft-edge/webview2/\n\n"
            "Después vuelve a abrir Netckore.",
            "Netckore - falta un componente",
        )
        return
    startup_log.log("WebView2 runtime found")

    TranslationManager()
    startup_log.log("translations loaded")

    lang = None
    saved_lang = load_config().get("language")
    if saved_lang and saved_lang in TranslationManager.get_available_languages():
        lang = saved_lang
        print(f"[i18n] Using saved language: {lang}")

    if lang is None:
        lang = TranslationManager.detect_system_language()
        print(f"[i18n] Auto-detected system language: {lang}")
    TranslationManager.set_language(lang)
    startup_log.log(f"language={lang}")

    api = Api()
    startup_log.log("api created")

    window = webview.create_window(
        "Netckore",
        html=_load_html(),
        js_api=api,
        width=1000,
        height=820,
        min_size=(900, 740),
        background_color="#050508",
    )
    api._window = window
    startup_log.log("window created (visible, dark background until the UI paints)")

    threading.Thread(target=_discard_legacy_profile, daemon=True).start()

    window.events.loaded += lambda *_: startup_log.log("window: loaded event")

    def _watchdog():
        if api._ready.wait(35):
            return
        startup_log.log("WATCHDOG: the page never reported ready")
        _show_message(
            "La interfaz de Netckore está tardando demasiado.\n\n"
            "Causas habituales:\n"
            "  - El runtime 'Microsoft Edge WebView2' está dañado.\n"
            "  - Un antivirus está bloqueando la aplicación.\n\n"
            f"Se guardó un diagnóstico en:\n{_export_diagnostics()}\n\n"
            "Envíame ese archivo para poder diagnosticarlo.",
            "Netckore - problema al iniciar",
        )

    threading.Thread(target=_watchdog, daemon=True).start()

    def _on_start():
        # pywebview runs this callback on its own thread; keep it tiny.
        startup_log.log("pywebview: start callback")
        threading.Thread(target=api._pusher, daemon=True).start()

    startup_log.log("entering pywebview.start()")
    try:
        # pywebview >= 4 understands these; pass only the ones it supports so
        # older versions still work.
        parameters = inspect.signature(webview.start).parameters
        start_kwargs = {}
        if "icon" in parameters:
            # pywebview 6 sets the form icon natively on the UI thread; doing
            # it ourselves through pythonnet was the only cross-thread WinForms
            # manipulation we had and it is not worth the risk.
            start_kwargs["icon"] = window_icon_path()
        if "private_mode" in parameters:
            start_kwargs["private_mode"] = False
        if "storage_path" in parameters:
            if profile_path:
                start_kwargs["storage_path"] = profile_path
        startup_log.log(f"webview.start() options: {sorted(start_kwargs)}")
        webview.start(_on_start, **start_kwargs)
    finally:
        startup_log.log("pywebview.start() returned (app closed)")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        startup_log.log_exception("CRITICAL: unhandled exception")
        _show_message(
            "Netckore no pudo iniciarse.\n\n"
            f"Detalle técnico guardado en:\n{startup_log.log_path()}",
            "Netckore - error crítico",
        )