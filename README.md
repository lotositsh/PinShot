# 📷 Screenshot Mini

A tiny, always-on-top Windows screenshot tool. Click the floating icon (or hit a global hotkey), drag to select a region, then upload it to [imgbb](https://imgbb.com/) or copy it straight to your clipboard — the URL lands on your clipboard automatically after upload.

## Features

- **Floating pill button** — small, draggable, always-on-top window that stays out of your way
- **Global hotkey** — trigger region selection from anywhere (`Ctrl+Alt` by default; also supports `PrintScreen`, `Alt+PrintScreen`, `F9`, `F10`, `F11`)
- **Region selection overlay**
  - Frozen or live desktop backdrop while dragging
  - Optional dimming of everything outside the selection
  - Optional live width × height readout
- **Two actions after selecting a region**
  - `S` or `Ctrl+D` / click ⬆ — upload to imgbb and copy the resulting link
  - `C` / click 📋 — copy the image directly to the clipboard (no upload)
- **Multiple imgbb API keys** — save several keys and switch between them from the tray menu
- **Configurable output format** — WEBP, PNG, or JPEG, with adjustable quality for lossy formats
- **Configurable link expiration** — from 5 minutes up to 3 months
- **Persistent settings** — everything is saved to a local JSON config file

## Requirements

- Windows (uses `pywin32` for clipboard access and `keyboard` for global hotkeys)
- Python 3.9+

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the app:
   ```bash
   python main.py
   ```
2. Right-click the floating icon → **Select API → Manage APIs...** to add your [imgbb API key](https://api.imgbb.com/).
3. Left-click the icon, or press the configured hotkey, to start a region selection.
4. Drag to select an area, then:
   - Click **⬆** (or press `S` / `Ctrl+D`) to upload — the link is copied to your clipboard automatically.
   - Click **📋** (or press `C`) to copy the image only.
   - Press `Esc` to cancel.

Right-click the icon at any time to change format, quality, hotkey, link expiration, or selection overlay behavior (dimming, freeze vs. live backdrop, size readout).

## Project structure

| File | Purpose |
|---|---|
| `main.py` | App entry point; wires everything together and handles the upload flow |
| `gui.py` | The floating button window and its right-click settings menu |
| `screenshot_taker.py` | Fullscreen region-selection overlay and its Upload/Copy controls |
| `image_processor.py` | Encodes the captured screenshot to WEBP/PNG/JPEG |
| `uploader.py` | Uploads the encoded image to imgbb |
| `dialogs.py` | API key management and quality settings dialogs |
| `config.py` | Loads/saves persistent settings to a local JSON file |

## Building a standalone executable

The project includes PyInstaller in its dependencies, so you can build a single-file `.exe`:

```bash
pyinstaller --onefile --noconsole --name ScreenshotMini main.py
```

## Configuration

Settings are stored in `screenshot_mini_settings.json` next to the app, including your saved API keys. Keep this file private if you share your project folder.

## License

Licensed under the GNU General Public License. See [LICENSE](LICENSE) for details.
