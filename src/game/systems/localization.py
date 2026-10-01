import json
import os
from pathlib import Path

from game.utils.paths import data_path


class Localization:
    def __init__(self, language=None):
        self.settings_path = Path(os.environ.get("APPDATA", Path.home())) / "Grimorium" / "settings.json"
        self.settings = {}
        try:
            settings = json.loads(self.settings_path.read_text(encoding="utf-8"))
            if isinstance(settings, dict):
                self.settings = settings
        except (OSError, ValueError):
            pass
        language = language or self.settings.get("language", "es")
        if language not in ("es", "en"):
            language = "es"
        self.language = language
        self.texts = {}
        self.load(language)

    def load(self, language):
        if language not in ("es", "en"):
            raise ValueError(f"Unsupported language: {language}")
        self.language = language

        path = data_path("lang", f"{language}.json")
        with open(path, "r", encoding="utf-8") as file:
            self.texts = json.load(file)

    def set_language(self, language):
        self.load(language)
        self.settings["language"] = language
        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.settings_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
            temporary.replace(self.settings_path)
            return True
        except OSError:
            return False

    def text(self, key, fallback=None):
        if fallback is None:
            fallback = key

        value = self.texts

        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                return fallback

            value = value[part]

        return value
