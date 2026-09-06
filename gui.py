import tkinter as tk
from tkinter import Menu

WINDOW_SIZE = 36
BTN_COLOR_OK = "#4CAF50"
BTN_COLOR_WARN = "#ff9800"
BTN_COLOR_ERROR = "#f44336"


class MainWindow:
    def __init__(self, config, on_select_region, on_manage_apis, on_quality_settings,
                 on_hotkey_change, on_exit=None):
        self.config = config
        self.on_select_region = on_select_region
        self.on_manage_apis = on_manage_apis
        self.on_quality_settings = on_quality_settings
        self.on_hotkey_change = on_hotkey_change
        self.on_exit = on_exit

        self.root = tk.Tk()
        self.root.title("📷")
        self.root.geometry(f"{WINDOW_SIZE}x{WINDOW_SIZE}")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)

        self.setup_button()
        self.setup_dragging()
        self.setup_context_menu()

        self.root.bind('<Escape>', lambda e: self.exit_app())

    def exit_app(self):
        if self.on_exit:
            self.on_exit()
        self.root.quit()
        self.root.destroy()

    def setup_button(self):
        self.btn = tk.Button(
            self.root,
            text="📷",
            font=("Arial", 13),
            command=self.on_select_region,
            bg=BTN_COLOR_OK,
            fg="white",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            activebackground="#45a049",
            activeforeground="white",
            width=2,
            height=1
        )
        self.btn.pack(fill=tk.BOTH, expand=True)

        if not self.config.apis:
            self.btn.config(bg=BTN_COLOR_WARN)

    def setup_dragging(self):
        def start_drag(event):
            self.root.x = event.x
            self.root.y = event.y

        def drag(event):
            deltax = event.x - self.root.x
            deltay = event.y - self.root.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")

        self.btn.bind("<ButtonPress-1>", start_drag)
        self.btn.bind("<B1-Motion>", drag)
        self.btn.bind("<Button-3>", lambda e: self.context_menu.post(e.x_root, e.y_root))

    def setup_context_menu(self):
        self.context_menu = Menu(self.root, tearoff=0)

        # API selection
        api_menu = Menu(self.context_menu, tearoff=0)
        for name in self.config.apis:
            api_menu.add_command(
                label=f"{'✓ ' if name == self.config.current_api else '  '}{name}",
                command=lambda n=name: self.select_api(n)
            )
        api_menu.add_separator()
        api_menu.add_command(label="Manage APIs...", command=self.on_manage_apis)
        self.context_menu.add_cascade(label="Select API", menu=api_menu)
        self.context_menu.add_separator()

        # Output format
        format_menu = Menu(self.context_menu, tearoff=0)
        formats = [("WEBP", "WEBP"), ("PNG", "PNG"), ("JPG", "JPEG")]
        for text, value in formats:
            format_menu.add_command(
                label=f"{'✓ ' if self.config.image_format == value else '  '}{text}",
                command=lambda v=value: self.set_format(v)
            )
        self.context_menu.add_cascade(label="Format", menu=format_menu)

        # Link expiration
        expiration_menu = Menu(self.context_menu, tearoff=0)
        self.expiration_options = {
            "5 minutes": 300,
            "15 minutes": 900,
            "30 minutes": 1800,
            "1 hour": 3600,
            "3 hours": 10800,
            "6 hours": 21600,
            "12 hours": 43200,
            "1 day": 86400,
            "2 days": 172800,
            "3 days": 259200,
            "4 days": 345600,
            "5 days": 432000,
            "6 days": 518400,
            "1 week": 604800,
            "2 weeks": 1209600,
            "3 weeks": 1814400,
            "1 month": 2592000,
            "2 months": 5184000,
            "3 months": 7776000,
        }
        for text, value in self.expiration_options.items():
            expiration_menu.add_command(
                label=f"{'✓ ' if value == self.config.expiration else '  '}{text}",
                command=lambda v=value: self.set_expiration(v)
            )
        self.context_menu.add_cascade(label="Expiration", menu=expiration_menu)

        self.context_menu.add_command(label="Quality...", command=lambda: self.on_quality_settings(self.root))

        # Selection overlay behavior
        selection_menu = Menu(self.context_menu, tearoff=0)
        self.dim_var = tk.BooleanVar(value=self.config.dim_selection)
        self.freeze_var = tk.BooleanVar(value=self.config.freeze_screen)
        self.size_label_var = tk.BooleanVar(value=self.config.show_size_label)

        selection_menu.add_checkbutton(
            label="Dim background (alpha)",
            variable=self.dim_var,
            command=self.toggle_dim_selection
        )
        selection_menu.add_checkbutton(
            label="Freeze screen while selecting",
            variable=self.freeze_var,
            command=self.toggle_freeze_screen
        )
        selection_menu.add_checkbutton(
            label="Show size readout",
            variable=self.size_label_var,
            command=self.toggle_show_size_label
        )
        self.context_menu.add_cascade(label="Selection", menu=selection_menu)
        self.context_menu.add_separator()

        # Hotkey - exactly one trigger for "select region"
        hotkeys_menu = Menu(self.context_menu, tearoff=0)
        self.hotkey_options = {
            "Ctrl+Alt": "ctrl+alt",
            "PrintScreen": "printscreen",
            "Alt+PrintScreen": "alt+printscreen",
            "F9": "f9",
            "F10": "f10",
            "F11": "f11",
        }
        for text, value in self.hotkey_options.items():
            hotkeys_menu.add_command(
                label=f"{'✓ ' if value == self.config.hotkey else '  '}{text}",
                command=lambda v=value: self.set_hotkey(v)
            )
        self.context_menu.add_cascade(label="Hotkey", menu=hotkeys_menu)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Exit", command=self.exit_app)

    def select_api(self, name):
        if name not in self.config.apis:
            return
        self.config.current_api = name
        self.config.save()
        self.btn.config(bg=BTN_COLOR_OK)
        self.setup_context_menu()

    def set_expiration(self, value):
        self.config.expiration = value
        self.config.save()
        self.setup_context_menu()

    def set_hotkey(self, value):
        # on_hotkey_change updates config, saves it, and re-registers the
        # global hotkey; we just rebuild the menu so the checkmark moves.
        self.on_hotkey_change(value)
        self.setup_context_menu()

    def set_format(self, format):
        self.config.image_format = format
        self.config.save()
        self.setup_context_menu()

    def toggle_dim_selection(self):
        self.config.dim_selection = self.dim_var.get()
        self.config.save()

    def toggle_freeze_screen(self):
        self.config.freeze_screen = self.freeze_var.get()
        self.config.save()

    def toggle_show_size_label(self):
        self.config.show_size_label = self.size_label_var.get()
        self.config.save()

    def run(self):
        self.root.mainloop()

    def withdraw(self):
        self.root.withdraw()

    def deiconify(self):
        self.root.deiconify()

    def show_notification(self, message, success=True):
        notification = tk.Toplevel(self.root)
        notification.overrideredirect(True)
        notification.attributes('-topmost', True)
        bg = '#333333' if success else BTN_COLOR_ERROR
        notification.configure(bg=bg)

        x = self.root.winfo_x()
        y = self.root.winfo_y() + 50
        notification.geometry(f"+{x}+{y}")

        tk.Label(
            notification,
            text=message,
            bg=bg,
            fg='white',
            padx=10,
            pady=5
        ).pack()

        notification.after(self.config.notification_duration, notification.destroy)
