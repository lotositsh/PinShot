import tkinter as tk
from tkinter import messagebox, Scale

BTN_STYLE = dict(relief=tk.FLAT, bd=0, fg="white", font=("Arial", 9), cursor="hand2", padx=10, pady=4)
COLOR_PRIMARY = "#4CAF50"
COLOR_PRIMARY_HOVER = "#45a049"
COLOR_DANGER = "#f44336"
COLOR_DANGER_HOVER = "#d32f2f"
COLOR_NEUTRAL = "#757575"
COLOR_NEUTRAL_HOVER = "#616161"


def _styled_button(parent, text, command, color, hover_color, width=8):
    btn = tk.Button(parent, text=text, command=command, bg=color, width=width, **BTN_STYLE)
    btn.bind("<Enter>", lambda e: btn.config(bg=hover_color))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


class Dialogs:
    def __init__(self, config, on_settings_changed):
        self.config = config
        self.on_settings_changed = on_settings_changed

    def show_api_warning(self, parent):
        messagebox.showwarning(
            "No API Configured",
            "Please add an API key via right-click menu -> Select API -> Manage APIs"
        )

    def open_quality_settings(self, parent):
        quality_window = tk.Toplevel(parent)
        quality_window.title("Quality Settings")
        quality_window.geometry("350x200")
        quality_window.resizable(False, False)
        quality_window.transient(parent)
        quality_window.grab_set()

        tk.Label(quality_window, text="Image Quality Settings",
                 font=("Arial", 12, "bold")).pack(pady=10)

        quality_frame = tk.Frame(quality_window)
        quality_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(quality_frame, text="Quality:").pack(anchor=tk.W)

        quality_value = tk.IntVar(value=self.config.quality)
        quality_label = tk.Label(quality_frame, text=f"{quality_value.get()}%")
        quality_label.pack()

        quality_slider = Scale(
            quality_frame,
            from_=50,
            to=100,
            orient=tk.HORIZONTAL,
            length=250,
            resolution=5,
            showvalue=0,
            variable=quality_value,
            command=lambda val: quality_label.config(text=f"{int(float(val))}%")
        )
        quality_slider.set(self.config.quality)
        quality_slider.pack(pady=5)

        info_label = tk.Label(
            quality_frame,
            text="Applies to WEBP and JPG formats only",
            font=("Arial", 8),
            fg="gray"
        )
        info_label.pack()

        btn_frame = tk.Frame(quality_window)
        btn_frame.pack(pady=15)

        def apply_quality():
            self.config.quality = quality_slider.get()
            self.config.save()
            info_label.config(text=f"✓ Quality set to {self.config.quality}% (saved)", fg="green")
            quality_window.after(1500, lambda: info_label.config(
                text="Applies to WEBP and JPG formats only", fg="gray"
            ))

        def save_and_close():
            self.config.quality = quality_slider.get()
            self.config.save()
            quality_window.destroy()
            self.on_settings_changed()

        _styled_button(btn_frame, "Apply", apply_quality, COLOR_PRIMARY, COLOR_PRIMARY_HOVER).pack(side=tk.LEFT, padx=4)
        _styled_button(btn_frame, "Save & Close", save_and_close, COLOR_PRIMARY, COLOR_PRIMARY_HOVER, width=11).pack(side=tk.LEFT, padx=4)
        _styled_button(btn_frame, "Cancel", quality_window.destroy, COLOR_NEUTRAL, COLOR_NEUTRAL_HOVER).pack(side=tk.LEFT, padx=4)

    def manage_apis(self, parent):
        api_window = tk.Toplevel(parent)
        api_window.title("API Management")
        api_window.geometry("300x400")
        api_window.resizable(False, False)
        api_window.transient(parent)
        api_window.grab_set()

        tk.Label(api_window, text="API Keys Management",
                 font=("Arial", 12, "bold")).pack(pady=10)

        list_frame = tk.Frame(api_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Label(list_frame, text="Saved APIs:").pack(anchor=tk.W)

        listbox = tk.Listbox(list_frame, height=8)
        listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        for name in self.config.apis:
            listbox.insert(tk.END, name)

        edit_frame = tk.Frame(api_window)
        edit_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(edit_frame, text="Name:").grid(row=0, column=0, sticky=tk.W)
        name_var = tk.StringVar()
        tk.Entry(edit_frame, textvariable=name_var, width=20).grid(row=0, column=1, padx=5, pady=2)

        tk.Label(edit_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        key_var = tk.StringVar()
        key_entry = tk.Entry(edit_frame, textvariable=key_var, width=30, show="*")
        key_entry.grid(row=1, column=1, padx=5, pady=2)

        def toggle_show():
            if key_entry.cget('show') == '*':
                key_entry.config(show='')
                show_btn.config(text='Hide')
            else:
                key_entry.config(show='*')
                show_btn.config(text='Show')

        show_btn = _styled_button(edit_frame, "Show", toggle_show, COLOR_NEUTRAL, COLOR_NEUTRAL_HOVER, width=5)
        show_btn.grid(row=1, column=2, padx=5)

        def on_select(event):
            selection = listbox.curselection()
            if selection:
                name = listbox.get(selection[0])
                name_var.set(name)
                key_var.set(self.config.apis[name])

        listbox.bind('<<ListboxSelect>>', on_select)

        btn_frame = tk.Frame(api_window)
        btn_frame.pack(pady=10)

        def save_api():
            name = name_var.get().strip()
            key = key_var.get().strip()

            if not name or not key:
                messagebox.showwarning("Warning", "Please enter both name and API key")
                return

            self.config.apis[name] = key
            if not self.config.current_api:
                self.config.current_api = name

            listbox.delete(0, tk.END)
            for api_name in self.config.apis:
                listbox.insert(tk.END, api_name)

            name_var.set("")
            key_var.set("")
            self.config.save()
            self.on_settings_changed()

        def delete_api():
            selection = listbox.curselection()
            if not selection:
                return

            name = listbox.get(selection[0])
            if not messagebox.askyesno("Confirm", f"Delete API '{name}'?"):
                return

            del self.config.apis[name]
            listbox.delete(selection[0])

            if self.config.current_api == name:
                self.config.current_api = next(iter(self.config.apis), None)

            self.config.save()
            self.on_settings_changed()

        def close_window():
            api_window.destroy()
            self.on_settings_changed()

        _styled_button(btn_frame, "Save", save_api, COLOR_PRIMARY, COLOR_PRIMARY_HOVER).pack(side=tk.LEFT, padx=4)
        _styled_button(btn_frame, "Delete", delete_api, COLOR_DANGER, COLOR_DANGER_HOVER).pack(side=tk.LEFT, padx=4)
        _styled_button(btn_frame, "Close", close_window, COLOR_NEUTRAL, COLOR_NEUTRAL_HOVER).pack(side=tk.LEFT, padx=4)
