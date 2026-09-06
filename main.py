# main.py
import threading

import pyperclip
import keyboard
from tkinter import messagebox

from config import Config
from uploader import ImageUploader
from screenshot_taker import ScreenshotTaker
from image_processor import ImageProcessor
from gui import MainWindow
from dialogs import Dialogs

# Maps the short id stored in config to the actual string the `keyboard`
# library expects for that combo/key.
HOTKEY_MAP = {
    "ctrl+alt": "ctrl+alt",
    "printscreen": "print screen",
    "alt+printscreen": "alt+print screen",
    "f9": "f9",
    "f10": "f10",
    "f11": "f11",
}


class ScreenshotApp:
    def __init__(self):
        self.config = Config()
        self.config.load()

        self.uploader = ImageUploader(self.config)
        self.image_processor = ImageProcessor(self.config)
        self.screenshot_taker = ScreenshotTaker(self.on_screenshot_taken, self.config)
        self.dialogs = Dialogs(self.config, self.on_settings_changed)

        self.gui = MainWindow(
            self.config,
            self.on_select_region,
            self.on_manage_apis,
            self.dialogs.open_quality_settings,
            self.on_hotkey_change,
            self.cleanup  # run before the window closes, however it closes
        )

        self.screenshot_taker.set_gui(self.gui)

        self._registered_hotkey_str = None
        self.setup_hotkeys()

        if not self.config.apis:
            self.gui.root.after(100, lambda: self.dialogs.show_api_warning(self.gui.root))

    def setup_hotkeys(self):
        """Register the global hotkey configured in config.hotkey."""
        hotkey_str = HOTKEY_MAP.get(self.config.hotkey, "ctrl+alt")
        try:
            keyboard.add_hotkey(hotkey_str, self.hotkey_callback)
            self._registered_hotkey_str = hotkey_str
            print(f"Hotkey registered: {hotkey_str} (region)")
        except Exception as e:
            print(f"Could not register hotkey '{hotkey_str}': {e}")
            print("Try running as administrator for global hotkeys")

    def on_hotkey_change(self, value):
        """Called from the GUI when the user picks a different hotkey."""
        if value not in HOTKEY_MAP:
            return

        self.config.hotkey = value
        self.config.save()

        # Unregister the old combo before registering the new one so only
        # one hotkey is ever active at a time.
        if self._registered_hotkey_str:
            try:
                keyboard.remove_hotkey(self._registered_hotkey_str)
            except KeyError:
                pass

        self.setup_hotkeys()

    def hotkey_callback(self):
        """Runs on the `keyboard` library's thread; hop back to the Tk thread."""
        self.gui.root.after(0, self.on_select_region)

    def cleanup(self):
        """Release global resources before the app closes."""
        try:
            keyboard.unhook_all()
        except Exception:
            pass

    def on_settings_changed(self):
        self.gui.setup_context_menu()

        if self.config.current_api and self.config.current_api in self.config.apis:
            self.gui.btn.config(bg="#4CAF50")
        elif not self.config.apis:
            self.gui.btn.config(bg="#ff9800")
        elif not self.config.current_api and self.config.apis:
            self.config.current_api = next(iter(self.config.apis))
            self.config.save()
            self.gui.btn.config(bg="#4CAF50")
        else:
            self.gui.btn.config(bg="#f44336")

    def on_select_region(self):
        if not self.config.current_api or self.config.current_api not in self.config.apis:
            messagebox.showwarning("No API", "Please configure an API first (right-click)")
            return

        self.gui.withdraw()
        self.screenshot_taker.select_region()

    def on_screenshot_taken(self, screenshot):
        # Always bring the floating icon back, regardless of outcome
        self.gui.deiconify()

        # screenshot is None when the user chose "copy" instead of "upload" -
        # that path is already fully handled by ScreenshotTaker
        if not screenshot:
            return

        try:
            image_bytes, size, file_size = self.image_processor.process_screenshot(screenshot)
            threading.Thread(
                target=self.upload_and_process,
                args=(image_bytes, size, file_size),
                daemon=True
            ).start()
        except Exception as e:
            self.gui.show_notification(f"Error: {str(e)}", success=False)
            self.gui.btn.config(bg="#f44336")
            self.gui.root.after(500, lambda: self.gui.btn.config(bg="#4CAF50"))

    def upload_and_process(self, image_bytes, size, file_size):
        url = self.uploader.upload_to_imgbb(image_bytes)
        self.gui.root.after(0, self.process_result, url, size, file_size)

    def process_result(self, url, size, file_size):
        if not url:
            self.gui.show_notification("Upload failed!", success=False)
            self.gui.btn.config(bg="#f44336")
            self.gui.root.after(500, lambda: self.gui.btn.config(bg="#4CAF50"))
            return

        pyperclip.copy(url)
        message = f"✓ Uploaded!\n{size[0]}x{size[1]} ({file_size} KB)\nURL copied to clipboard"
        self.gui.show_notification(message, success=True)
        self.gui.btn.config(bg="#8BC34A")
        self.gui.root.after(500, lambda: self.gui.btn.config(bg="#4CAF50"))

    def on_manage_apis(self):
        self.dialogs.manage_apis(self.gui.root)

    def run(self):
        self.gui.run()


if __name__ == "__main__":
    app = ScreenshotApp()
    app.run()
