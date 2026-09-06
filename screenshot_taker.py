# screenshot_taker.py
import io
import tkinter as tk

from PIL import ImageGrab, ImageTk
import win32clipboard

# Small on-canvas action buttons shown once a region is selected
BTN_SIZE = 32
BTN_RADIUS = 9
BTN_SPACING = 8
BTN_MARGIN = 15

# Size readout ("W x H"): tiny white digits on a solid black plate
SIZE_LABEL_FONT = ("Arial", 8)
SIZE_LABEL_PAD_X = 5
SIZE_LABEL_PAD_Y = 3
SIZE_LABEL_OFFSET_X = 14
SIZE_LABEL_OFFSET_Y = 16

# Windows virtual-key codes for S, C and D. Bound by keycode rather than
# keysym so the shortcuts fire from the physical key regardless of which
# keyboard layout (Cyrillic, etc.) is currently active - a layout only
# remaps which *character* a key produces, not its keycode.
VK_S = 0x53
VK_C = 0x43
VK_D = 0x44

# Control bit in Tkinter's event.state on Windows.
CTRL_STATE_MASK = 0x0004


class ScreenshotTaker:
    def __init__(self, on_complete_callback, config):
        self.on_complete = on_complete_callback
        self.config = config
        self.is_selecting = False
        self.selection_window = None
        self.canvas = None
        self.start_x = self.start_y = None
        self.rect = None
        self.tk_image = None
        self.image_item = None
        self.frozen = True
        self.screenshot = None
        self.selection_coords = None
        self.has_selection = False
        self.action = None
        self.gui = None  # set via set_gui() so we can show notifications

    def set_gui(self, gui):
        self.gui = gui

    def select_region(self):
        """Let the user drag out a region to select. If config.freeze_screen
        is on, the backdrop is a static snapshot. If off, no backdrop image
        is shown at all - the overlay window is made translucent instead
        (real Tk window alpha), so the live desktop shows straight through.
        In live mode the overlay turns opaque (snapshot + full alpha) as
        soon as the region is released, so the action buttons render at
        full strength instead of being faded out by the window alpha."""
        self.is_selecting = True
        self.action = None
        self.has_selection = False

        try:
            # Always grab a snapshot - even in live mode we need the pixel
            # data for the size-readout plate and the screen dimensions for
            # laying out the dim overlay.
            self.screenshot = ImageGrab.grab(all_screens=True)

            self.selection_window = tk.Toplevel()
            self.selection_window.attributes("-fullscreen", True)
            self.selection_window.attributes("-topmost", True)
            self.selection_window.overrideredirect(True)
            self.selection_window.configure(bg="black")

            self.canvas = tk.Canvas(
                self.selection_window, highlightthickness=0, cursor="cross", bg="black"
            )
            self.canvas.pack(fill="both", expand=True)

            if self.config.freeze_screen:
                self.frozen = True
                self.tk_image = ImageTk.PhotoImage(self.screenshot)
                self.image_item = self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
            else:
                self.frozen = False
                self.selection_window.update_idletasks()
                try:
                    # `-alpha` dims the whole window uniformly. While the
                    # user is still dragging this is fine (only the faint
                    # size plate suffers), and once the region is released
                    # _make_overlay_opaque() restores full opacity so the
                    # action buttons are clearly visible.
                    alpha = 0.30 if self.config.dim_selection else 0.15
                    self.selection_window.attributes("-alpha", alpha)
                except tk.TclError as e:
                    # Not supported on this Tk build - fall back to a
                    # frozen snapshot rather than show an unusable overlay.
                    print(f"Live mode unavailable ({e}), falling back to frozen")
                    self.frozen = True
                    self.tk_image = ImageTk.PhotoImage(self.screenshot)
                    self.image_item = self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
        except Exception as e:
            # Setup failed before anything was shown - make sure the tray
            # icon still comes back instead of staying hidden forever.
            print(f"Failed to open selection overlay: {e}")
            self.is_selecting = False
            if self.selection_window:
                try:
                    self.selection_window.destroy()
                except Exception:
                    pass
                self.selection_window = None
            self.on_complete(None)
            return

        self._update_dim(0, 0, 0, 0)

        self.canvas.bind("<ButtonPress-1>", self._mouse_down)
        self.canvas.bind("<B1-Motion>", self._mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._mouse_up)

        self.selection_window.bind("<KeyPress>", self._on_key_press)
        self.selection_window.bind("<Escape>", lambda e: self._cancel())

        self.selection_window.focus_force()
        self.selection_window.mainloop()

    def _on_key_press(self, event):
        if event.keycode == VK_S:
            self._on_action("upload")
        elif event.keycode == VK_D and (event.state & CTRL_STATE_MASK):
            self._on_action("upload")
        elif event.keycode == VK_C:
            self._on_action("copy")

    def _mouse_down(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="#00ff00", width=2, fill="", tags="selection"
        )
        self.has_selection = False
        self.canvas.delete("controls")
        self.canvas.tag_raise("selection")

    def _mouse_move(self, event):
        if not self.rect:
            return

        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        self.canvas.coords(self.rect, x1, y1, x2, y2)
        self._update_dim(x1, y1, x2, y2)

        w, h = abs(event.x - self.start_x), abs(event.y - self.start_y)
        self.canvas.delete("size_text")

        if self.config.show_size_label:
            self._draw_size_label(event.x, event.y, w, h)

        self.canvas.tag_raise("selection")
        self.canvas.tag_raise("size_text")

        self.selection_coords = (x1, y1, x2, y2)
        self.has_selection = True

    def _draw_size_label(self, mx, my, w, h):
        """Draw a compact black plate with the selection size in small
        white digits next to the cursor. The solid black background keeps
        the numbers legible on any desktop content, so no per-pixel
        contrast detection is required."""
        label = f"{w} x {h}"

        # Measure the rendered text so the plate hugs the digits tightly
        probe = self.canvas.create_text(0, 0, text=label, font=SIZE_LABEL_FONT)
        bb = self.canvas.bbox(probe)
        self.canvas.delete(probe)
        text_w = bb[2] - bb[0]
        text_h = bb[3] - bb[1]
        half_w = text_w / 2 + SIZE_LABEL_PAD_X
        half_h = text_h / 2 + SIZE_LABEL_PAD_Y

        cx = mx + SIZE_LABEL_OFFSET_X
        cy = my - SIZE_LABEL_OFFSET_Y

        # Flip to the left / below the cursor when nearing a screen edge
        if cx + half_w > self.screenshot.width - 2:
            cx = mx - SIZE_LABEL_OFFSET_X - half_w
        if cy - half_h < 2:
            cy = my + SIZE_LABEL_OFFSET_Y + half_h

        self.canvas.create_rectangle(
            cx - half_w, cy - half_h, cx + half_w, cy + half_h,
            fill="black", outline="#555555", width=1,
            tags="size_text"
        )
        self.canvas.create_text(
            cx, cy,
            text=label,
            fill="white",
            font=SIZE_LABEL_FONT,
            tags="size_text"
        )

    def _update_dim(self, x1, y1, x2, y2):
        """Redraw the dimmed overlay around the selected region (4 shaded
        rects), if config.dim_selection is enabled. Works in both frozen
        and live mode - in live mode this stacks on top of the window's
        own base alpha (set once in select_region()) to make the area
        outside the selection read as darker than the area inside it."""
        self.canvas.delete("alpha")

        if not self.config.dim_selection:
            self.canvas.tag_raise("selection")
            self.canvas.tag_raise("size_text")
            self.canvas.tag_raise("controls")
            return

        w, h = self.screenshot.width, self.screenshot.height
        for coords in (
            (0, 0, w, y1),      # top
            (0, y2, w, h),      # bottom
            (0, y1, x1, y2),    # left
            (x2, y1, w, y2),    # right
        ):
            self.canvas.create_rectangle(
                *coords, fill="black", stipple="gray25", width=0, tags="alpha"
            )

        self.canvas.tag_raise("alpha")
        self.canvas.tag_raise("selection")
        self.canvas.tag_raise("size_text")
        self.canvas.tag_raise("controls")

    def _mouse_up(self, event):
        if not self.rect:
            return

        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)

        if x2 - x1 < 10 or y2 - y1 < 10:
            self._cancel()
            return

        self.selection_coords = (x1, y1, x2, y2)
        self.has_selection = True

        self.canvas.itemconfig(self.rect, outline="#00ff00", width=3)

        # Live (nofreeze) mode dims the entire overlay window with -alpha,
        # which fades the action buttons out as well. Nothing needs to stay
        # live once the region is fixed, so switch to the opaque snapshot
        # before drawing the controls.
        if not self.frozen:
            self._make_overlay_opaque()

        self._show_controls()

    def _make_overlay_opaque(self):
        """Drop the window-wide transparency used by live mode and paint
        the pre-grabbed fullscreen snapshot instead, so widgets drawn on
        the canvas (Upload/Copy buttons, tooltip) render at full opacity."""
        try:
            self.selection_window.attributes("-alpha", 1.0)
        except tk.TclError:
            pass
        self.tk_image = ImageTk.PhotoImage(self.screenshot)
        self.image_item = self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
        # Keep the snapshot underneath the selection rect, dim plates and buttons
        self.canvas.tag_lower(self.image_item)
        self.frozen = True

    def _round_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Draw a rounded rectangle as a smoothed polygon."""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def _show_controls(self):
        """Draw the compact Upload/Copy buttons beside the selected region."""
        if not self.has_selection or not self.selection_coords:
            return

        x1, y1, x2, y2 = self.selection_coords

        btn_x = x2 + BTN_MARGIN
        btn_y = y1 + (y2 - y1 - BTN_SIZE * 2 - BTN_SPACING) // 2

        # Flip to the left side if there's no room on the right
        if btn_x + BTN_SIZE > self.screenshot.width:
            btn_x = x1 - BTN_SIZE - BTN_MARGIN
            if btn_x < 0:
                btn_x, btn_y = 10, y1

        self.canvas.delete("controls")
        self.canvas.delete("tooltip")

        # Upload button
        self._round_rect(
            btn_x, btn_y, btn_x + BTN_SIZE, btn_y + BTN_SIZE, BTN_RADIUS,
            fill="#28a745", outline="#45c463", width=2,
            tags=("controls", "s_btn")
        )
        self.canvas.create_text(
            btn_x + BTN_SIZE // 2, btn_y + BTN_SIZE // 2,
            text="⬆", font=("Segoe UI Symbol", 15, "bold"),
            fill="white", tags=("controls", "s_text")
        )

        # Copy button
        copy_y = btn_y + BTN_SIZE + BTN_SPACING
        self._round_rect(
            btn_x, copy_y, btn_x + BTN_SIZE, copy_y + BTN_SIZE, BTN_RADIUS,
            fill="#0A84FF", outline="#4DA3FF", width=2,
            tags=("controls", "c_btn")
        )
        self.canvas.create_text(
            btn_x + BTN_SIZE // 2, copy_y + BTN_SIZE // 2,
            text="📋", font=("Segoe UI Emoji", 14),
            fill="white", tags=("controls", "c_text")
        )

        self._bind_button("s_btn", "s_text", "upload", "Upload", "#28a745", "#34c759")
        self._bind_button("c_btn", "c_text", "copy", "Copy", "#0A84FF", "#3B9DFF")

        self.canvas.tag_raise("controls")

    def _bind_button(self, shape_tag, text_tag, action, tooltip, base_color, hover_color):
        """Wire click/hover behaviour for one action button (shared by
        both its shape and its label so the whole button area is clickable)."""
        for tag in (shape_tag, text_tag):
            self.canvas.tag_bind(tag, "<Button-1>", lambda e: self._on_action(action))

        def on_enter(e):
            self.canvas.itemconfig(shape_tag, fill=hover_color)
            self._show_tooltip(e, tooltip)
            self.canvas.config(cursor="hand2")

        def on_leave(e):
            self.canvas.itemconfig(shape_tag, fill=base_color)
            self._hide_tooltip()
            self.canvas.config(cursor="cross")

        for tag in (shape_tag, text_tag):
            self.canvas.tag_bind(tag, "<Enter>", on_enter)
            self.canvas.tag_bind(tag, "<Leave>", on_leave)

    def _show_tooltip(self, event, text):
        self.canvas.delete("tooltip")

        x, y = event.x + 15, event.y - 10
        self.canvas.create_rectangle(
            x - 5, y - 18, x + len(text) * 6 + 10, y + 5,
            fill="#2d2d2d", outline="#555", width=1,
            tags="tooltip"
        )
        self.canvas.create_text(
            x + len(text) * 3, y - 5,
            text=text, fill="white", font=("Arial", 9),
            tags="tooltip"
        )

    def _hide_tooltip(self):
        self.canvas.delete("tooltip")

    def _on_action(self, action):
        if not self.has_selection or not self.selection_coords:
            return

        x1, y1, x2, y2 = self.selection_coords
        self.action = action

        if self.selection_window:
            self.selection_window.destroy()
            self.selection_window = None
        self.is_selecting = False

        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))

        if action == "copy":
            self._copy_to_clipboard(screenshot)
            if self.gui:
                self.gui.show_notification("✓ Copied!", success=True)
            self.on_complete(None)
        else:
            self.on_complete(screenshot)

    def _copy_to_clipboard(self, image):
        try:
            output = io.BytesIO()
            image.save(output, format="DIB")

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, output.getvalue())
            win32clipboard.CloseClipboard()
        except Exception as e:
            print(f"Failed to copy to clipboard: {e}")

    def _cancel(self):
        if self.selection_window:
            self.selection_window.destroy()
            self.selection_window = None
        self.is_selecting = False
        self.on_complete(None)
