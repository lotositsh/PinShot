import json
import os

SETTINGS_FILE = "screenshot_mini_settings.json"


class Config:
    def __init__(self):
        self.apis = {}
        self.current_api = None
        self.image_format = "WEBP"
        self.quality = 90
        self.notification_duration = 2000
        self.expiration = 2592000  # 30 days in seconds
        self.hotkey = "ctrl+alt"  # one of: ctrl+alt, printscreen, alt+printscreen, f9, f10, f11
        self.dim_selection = True  # dim (alpha-shade) everything outside the selected region
        self.freeze_screen = True  # show a frozen snapshot while selecting vs. the live desktop
        self.show_size_label = True  # show the W x H readout while dragging the selection

    def load(self):
        if not os.path.exists(SETTINGS_FILE):
            return
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
        except (OSError, json.JSONDecodeError):
            return

        self.apis = settings.get("apis", {})
        self.current_api = settings.get("current_api")
        self.image_format = settings.get("image_format", "WEBP")
        self.quality = settings.get("quality", 90)
        self.notification_duration = settings.get("notification_duration", 2000)
        self.expiration = settings.get("expiration", 2592000)
        self.hotkey = settings.get("hotkey", "ctrl+alt")
        self.dim_selection = settings.get("dim_selection", True)
        self.freeze_screen = settings.get("freeze_screen", True)
        self.show_size_label = settings.get("show_size_label", True)

        if self.current_api not in self.apis and self.apis:
            self.current_api = next(iter(self.apis))

    def save(self):
        settings = {
            "apis": self.apis,
            "current_api": self.current_api,
            "image_format": self.image_format,
            "quality": self.quality,
            "notification_duration": self.notification_duration,
            "expiration": self.expiration,
            "hotkey": self.hotkey,
            "dim_selection": self.dim_selection,
            "freeze_screen": self.freeze_screen,
            "show_size_label": self.show_size_label,
        }
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(settings, f)
        except OSError:
            pass
