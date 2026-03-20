import ctypes
import json
import os
import re
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from windows_toasts import (
    InteractableWindowsToaster,
    Toast,
    ToastActivatedEventArgs,
    ToastButton,
    ToastDisplayImage,
    ToastImagePosition,
    WindowsToaster,
)


DEFAULT_APP_NAME = "Command Prompt"
DEFAULT_APP_ID = r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\cmd.exe"
WINDOW_TITLE = "ToastGeneratorReal"
MIN_FULL_FEATURED_BUILD = 10074
IMAGE_TYPE_OPTIONS = [
    ("No image", "none"),
    ("Inline image", ToastImagePosition.Inline),
    ("Hero image", ToastImagePosition.Hero),
    ("App logo", ToastImagePosition.AppLogo),
]


def windows_build_number() -> int:
    return sys.getwindowsversion().build


def load_start_apps() -> list[dict[str, str]]:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-StartApps | Sort-Object Name | Select-Object Name, AppID | ConvertTo-Json -Depth 2",
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return [{"Name": DEFAULT_APP_NAME, "AppID": DEFAULT_APP_ID}]

    payload = result.stdout.strip()
    if not payload:
        return [{"Name": DEFAULT_APP_NAME, "AppID": DEFAULT_APP_ID}]

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return [{"Name": DEFAULT_APP_NAME, "AppID": DEFAULT_APP_ID}]

    if isinstance(data, dict):
        data = [data]

    apps = []
    for item in data:
        name = str(item.get("Name", "")).strip()
        app_id = str(item.get("AppID", "")).strip()
        if name and app_id:
            apps.append({"Name": name, "AppID": app_id})

    return apps or [{"Name": DEFAULT_APP_NAME, "AppID": DEFAULT_APP_ID}]


class ToastGeneratorApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry("760x560")
        self.root.minsize(700, 520)

        self.start_apps = load_start_apps()
        self.app_lookup = {
            f"{item['Name']} [{item['AppID']}]": item for item in self.start_apps
        }

        self.app_name_var = tk.StringVar(value=DEFAULT_APP_NAME)
        self.app_id_var = tk.StringVar(value=DEFAULT_APP_ID)
        self.title_var = tk.StringVar(value="Title")
        self.button1_var = tk.StringVar()
        self.button2_var = tk.StringVar()
        self.image1_var = tk.StringVar()
        self.image2_var = tk.StringVar()
        self.image_type1_var = tk.StringVar(value="No image")
        self.image_type2_var = tk.StringVar(value="No image")
        self.status_var = tk.StringVar(value="Ready.")

        self.build_ui()

    def build_ui(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        creator_tab = ttk.Frame(notebook, padding=12)
        about_tab = ttk.Frame(notebook, padding=12)
        notebook.add(creator_tab, text="Notification Creator")
        notebook.add(about_tab, text="About")

        ttk.Label(creator_tab, text=WINDOW_TITLE, font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 10)
        )

        self.add_entry_row(creator_tab, 1, "Toast source name:", self.app_name_var)
        self.add_app_id_row(creator_tab, 2)
        self.add_entry_row(creator_tab, 3, "Notification title:", self.title_var)
        self.add_text_row(creator_tab, 4, "Notification text:")
        self.add_image_row(creator_tab, 5, "Image 1:", self.image1_var, self.image_type1_var)
        self.add_image_row(creator_tab, 6, "Image 2:", self.image2_var, self.image_type2_var)
        self.add_entry_row(creator_tab, 7, "Button 1:", self.button1_var)
        self.add_entry_row(creator_tab, 8, "Button 2:", self.button2_var)

        send_button = ttk.Button(creator_tab, text="Create notification", command=self.send_toast)
        send_button.grid(row=9, column=0, columnspan=3, sticky="ew", pady=(12, 8))

        ttk.Label(creator_tab, textvariable=self.status_var, wraplength=680).grid(
            row=10, column=0, columnspan=3, sticky="w", pady=(4, 6)
        )
        ttk.Label(
            creator_tab,
            text=(
                "Pick a real Windows AppUserModelID from the list or type one manually. "
                "Builds older than Windows 10 build 10074 use reduced compatibility mode."
            ),
            wraplength=680,
        ).grid(row=11, column=0, columnspan=3, sticky="w")

        creator_tab.columnconfigure(1, weight=1)

        ttk.Label(
            about_tab,
            text="this made my @pixxxxyll (Effan), ps this not virus 😂😂🐓🐓🤣🤣🤣🤣🤣🤣",
            wraplength=660,
        ).pack(anchor="w")

    def add_entry_row(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)

    def add_text_row(self, parent: ttk.Frame, row: int, label: str) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=4)
        self.message_text = tk.Text(parent, height=5, width=50)
        self.message_text.insert("1.0", "Text")
        self.message_text.grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)

    def add_app_id_row(self, parent: ttk.Frame, row: int) -> None:
        ttk.Label(parent, text="Custom AppUserModelID:").grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=4
        )
        self.app_id_combo = ttk.Combobox(
            parent,
            textvariable=self.app_id_var,
            values=[f"{item['Name']} [{item['AppID']}]" for item in self.start_apps],
        )
        self.app_id_combo.grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)
        self.app_id_combo.bind("<<ComboboxSelected>>", self.sync_selected_app)
        self.app_id_combo.bind("<FocusOut>", self.sync_manual_app_id)

    def add_image_row(
            self,
            parent: ttk.Frame,
            row: int,
            label: str,
            path_var: tk.StringVar,
            type_var: tk.StringVar,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)

        row_frame = ttk.Frame(parent)
        row_frame.grid(row=row, column=1, sticky="ew", pady=4)
        row_frame.columnconfigure(0, weight=1)

        ttk.Entry(row_frame, textvariable=path_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(row_frame, text="Browse", command=lambda: self.browse_image(path_var)).grid(
            row=0, column=1, padx=(6, 0)
        )

        combo = ttk.Combobox(parent, textvariable=type_var, values=[label for label, _ in IMAGE_TYPE_OPTIONS], state="readonly")
        combo.grid(row=row, column=2, sticky="ew", pady=4, padx=(8, 0))

    def browse_image(self, target_var: tk.StringVar) -> None:
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif")],
        )
        if file_path:
            target_var.set(file_path)

    def current_app_id(self) -> str:
        text = self.app_id_var.get().strip()
        match = re.search(r"\[(.+)\]$", text)
        if match:
            return match.group(1).strip()
        return text

    def sync_selected_app(self, _event=None) -> None:
        selected = self.app_lookup.get(self.app_id_var.get().strip())
        if selected:
            self.app_name_var.set(selected["Name"])
            self.app_id_var.set(selected["AppID"])

    def sync_manual_app_id(self, _event=None) -> None:
        raw_app_id = self.current_app_id()
        if not raw_app_id:
            return
        for item in self.start_apps:
            if item["AppID"] == raw_app_id:
                self.app_name_var.set(item["Name"])
                return

    def attach_images(self, toast: Toast) -> str | None:
        image_entries = [
            ("Image 1", self.image1_var.get().strip(), self.image_type1_var.get().strip()),
            ("Image 2", self.image2_var.get().strip(), self.image_type2_var.get().strip()),
        ]

        selected_positions = []
        build_number = windows_build_number()
        for label, path, type_label in image_entries:
            if not path or type_label == "No image":
                continue

            position = dict(IMAGE_TYPE_OPTIONS)[type_label]
            if position in selected_positions:
                return "Image 1 and Image 2 cannot use the same image type."
            if build_number < MIN_FULL_FEATURED_BUILD and selected_positions:
                return "Older Windows builds only support one image in compatibility mode."

            absolute_path = os.path.abspath(path)
            if not os.path.exists(absolute_path):
                return f"{label} not found: {absolute_path}"

            selected_positions.append(position)
            toast.AddImage(
                ToastDisplayImage.fromPath(
                    absolute_path,
                    position=position,
                    altText=label,
                )
            )

        return None

    def attach_buttons(self, toast: Toast) -> None:
        button1 = self.button1_var.get().strip()
        button2 = self.button2_var.get().strip()
        if button1:
            toast.AddAction(ToastButton(button1, arguments="action=1"))
        if button2:
            toast.AddAction(ToastButton(button2, arguments="action=2"))

    def handle_activated(self, event: ToastActivatedEventArgs | None) -> None:
        if event and event.arguments:
            self.status_var.set(f"Toast action clicked: {event.arguments}")
        else:
            self.status_var.set("Toast clicked.")

    def show_error(self, message: str) -> None:
        self.status_var.set(message)
        messagebox.showwarning(WINDOW_TITLE, message)

    def send_toast(self) -> None:
        app_name = self.app_name_var.get().strip() or DEFAULT_APP_NAME
        app_id = self.current_app_id()
        if not app_id:
            self.show_error("Enter a Windows AppUserModelID or choose one from the list.")
            return

        title = self.title_var.get().strip() or "Title"
        message = self.message_text.get("1.0", "end-1c").strip() or "Text"
        build_number = windows_build_number()

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        if build_number >= MIN_FULL_FEATURED_BUILD:
            toaster = InteractableWindowsToaster(app_name, app_id)
            supports_actions = True
        else:
            toaster = WindowsToaster(app_name)
            supports_actions = False

        toast = Toast()
        toast.text_fields = [title, message]
        toast.on_activated = self.handle_activated
        toast.on_dismissed = lambda _: self.status_var.set("Toast dismissed.")
        toast.on_failed = lambda event: self.status_var.set(f"Toast failed: {event}")

        image_error = self.attach_images(toast)
        if image_error:
            self.show_error(image_error)
            return

        if supports_actions:
            self.attach_buttons(toast)

        toaster.show_toast(toast)
        if build_number >= MIN_FULL_FEATURED_BUILD:
            self.status_var.set(f"Sent toast as '{app_name}' using AppID '{app_id}'.")
        else:
            self.status_var.set(
                f"Sent compatibility toast for Windows build {build_number}. "
                "Buttons and some advanced identity features are disabled."
            )

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    app = ToastGeneratorApp()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
