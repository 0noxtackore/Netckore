"""Translation manager (más idiomas) para Netckore."""
import os
import json
import locale

LANGUAGE_OPTIONS = {
    "es": {"name": "Español", "native": "Español"},
    "en": {"name": "English", "native": "English"},
    "fr": {"name": "Français", "native": "Français"},
    "de": {"name": "Deutsch", "native": "Deutsch"},
    "pt": {"name": "Português", "native": "Português"},
    "it": {"name": "Italiano", "native": "Italiano"},
    "ru": {"name": "Русский", "native": "Русский"},
    "ja": {"name": "日本語", "native": "日本語"},
    "zh": {"name": "中文", "native": "中文"},
    "ko": {"name": "한국어", "native": "한국어"},
    "ar": {"name": "العربية", "native": "العربية"},
}


class TranslationManager:
    _instance = None
    _current = "es"
    _translations = {}
    _available = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        # Minimal: cargar desde locales/translations.json
        path = os.path.join(os.path.dirname(__file__), "..", "locales", "translations.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._available = list(data.keys())
                # Usar español como base cuando se necesita una traducción faltante
                self._translations = data.get("es", {})
        else:
            self._translations = {}
            self._available = ["es", "en"]

    @classmethod
    def get_current_language(cls):
        return cls._current

    @classmethod
    def get_available_languages(cls):
        return cls._available

    @classmethod
    def get_translations(cls):
        return cls._translations

    @classmethod
    def set_language(cls, code):
        if code not in cls._available:
            return False
        cls._current = code
        # Cargar traducciones para este idioma
        try:
            path = os.path.join(os.path.dirname(__file__), "..", "locales", "translations.json")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if code in data:
                cls._translations = data[code]
        except Exception:
            pass
        return True

    @classmethod
    def detect_system_language(cls):
        try:
            lang = locale.getdefaultlocale()[0]
            if lang:
                code = lang.split("_")[0].lower()
                if code in LANGUAGE_OPTIONS:
                    return code
        except Exception:
            pass
        return "es"


_ = lambda key: TranslationManager._translations.get(key, key)