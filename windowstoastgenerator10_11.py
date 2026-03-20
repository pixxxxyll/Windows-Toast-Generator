"""
ToastGeneratorReal
==================
\\ can i get a big mac
"""

import ctypes
import json
import os
import re
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from xml.sax.saxutils import escape as xml_escape

BUILD_RAW_MIN  = 10074   
BUILD_LIB_MIN  = 10240   

DEFAULT_APP_NAME = "Command Prompt"
DEFAULT_APP_ID   = r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\cmd.exe"
WINDOW_TITLE     = "ToastGeneratorReal"

IMAGE_TYPE_OPTIONS: list[tuple[str, str]] = [
    ("No image",     "none"),
    ("Inline image", "Inline"),
    ("Hero image",   "Hero"),
    ("App logo",     "AppLogo"),
]
IMAGE_TYPE_LABELS = [label for label, _ in IMAGE_TYPE_OPTIONS]

_WINDOWS_TOASTS_OK = False
_POSITION_MAP: dict[str, object] = {}

if sys.getwindowsversion().build >= BUILD_LIB_MIN:
    try:
        from windows_toasts import (          
            InteractableWindowsToaster,
            Toast,
            ToastActivatedEventArgs,
            ToastButton,
            ToastDisplayImage,
            ToastImagePosition,
            WindowsToaster,
        )
        _POSITION_MAP = {
            "Inline":  ToastImagePosition.Inline,
            "Hero":    ToastImagePosition.Hero,
            "AppLogo": ToastImagePosition.AppLogo,
        }
        _WINDOWS_TOASTS_OK = True
    except Exception:
        pass

def windows_build_number() -> int:
    return sys.getwindowsversion().build


def is_supported_build() -> bool:
    """True for Windows 10 build 10074 through Windows 11."""
    return windows_build_number() >= BUILD_RAW_MIN


def uses_raw_winrt() -> bool:
    """True on builds 10074-10239 where windows-toasts cannot be used."""
    return BUILD_RAW_MIN <= windows_build_number() < BUILD_LIB_MIN


def _raw_winrt_toast(app_id: str, title: str, body: str) -> str | None:
    """
    Fire a basic toast via the WinRT COM ABI using only ctypes.
    Returns None on success, or an error string on failure.
    """
    try:
        combase = ctypes.windll.combase
        combase.RoInitialize(1)  

        def _hstr(s: str) -> ctypes.c_void_p:
            h = ctypes.c_void_p(0)
            combase.WindowsCreateString(
                ctypes.c_wchar_p(s), ctypes.c_uint32(len(s)), ctypes.byref(h)
            )
            return h

        def _free(h: ctypes.c_void_p) -> None:
            combase.WindowsDeleteString(h)

        def _vt(ptr: ctypes.c_void_p):
            return ctypes.cast(
                ctypes.cast(ptr, ctypes.POINTER(ctypes.c_void_p))[0],
                ctypes.POINTER(ctypes.c_void_p),
            )

        def _factory(cls_name: str, iid: list[int]):
            h   = _hstr(cls_name)
            iid_t = (ctypes.c_byte * 16)(*iid)
            ptr = ctypes.c_void_p(0)
            hr  = combase.RoGetActivationFactory(h, ctypes.byref(iid_t), ctypes.byref(ptr))
            _free(h)
            if hr != 0:
                raise OSError(f"RoGetActivationFactory({cls_name}) → 0x{hr & 0xFFFFFFFF:08X}")
            return ptr

        xml = (
            "<toast><visual><binding template='ToastGeneric'>"
            f"<text>{xml_escape(title)}</text>"
            f"<text>{xml_escape(body)}</text>"
            "</binding></visual></toast>"
        )


        mgr = _factory(
            "Windows.UI.Notifications.ToastNotificationManager",
            [0x3F,0x10,0xAC,0x50,0x35,0xD2,0x98,0x45,
             0xBB,0xEF,0x98,0xFE,0x4D,0x1A,0x3A,0xD4],
        )
        _Fn3 = ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p)
        )
        h_id    = _hstr(app_id)
        notifier = ctypes.c_void_p(0)
        hr = _Fn3(_vt(mgr)[6])(mgr, h_id, ctypes.byref(notifier))
        _free(h_id)
        if hr != 0:
            raise OSError(f"CreateToastNotifierWithId → 0x{hr & 0xFFFFFFFF:08X}")

        xf = _factory(
            "Windows.Data.Xml.Dom.XmlDocument",
            [0x06,0xA5,0xF3,0xF7,0x87,0x1E,0xD6,0x42,
             0xBC,0xFB,0xB8,0xC8,0x09,0xFA,0x54,0x94],
        )
        _Activate = ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)
        )
        xml_doc = ctypes.c_void_p(0)
        hr = _Activate(_vt(xf)[6])(xf, ctypes.byref(xml_doc))
        if hr != 0:
            raise OSError(f"XmlDocument ActivateInstance → 0x{hr & 0xFFFFFFFF:08X}")

        iid_io = (ctypes.c_byte * 16)(
            0x4E,0xE7,0xD0,0x6C,0x65,0xEE,0x89,0x44,
            0x9E,0xBF,0xCA,0x43,0xE8,0x7B,0xA6,0x37,
        )
        _QI = ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_byte * 16), ctypes.POINTER(ctypes.c_void_p)
        )
        xml_io = ctypes.c_void_p(0)
        hr = _QI(_vt(xml_doc)[0])(xml_doc, ctypes.byref(iid_io), ctypes.byref(xml_io))
        if hr != 0:
            raise OSError(f"QI IXmlDocumentIO → 0x{hr & 0xFFFFFFFF:08X}")

        _Load = ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, ctypes.c_void_p
        )
        h_xml = _hstr(xml)
        hr    = _Load(_vt(xml_io)[6])(xml_io, h_xml)
        _free(h_xml)
        if hr != 0:
            raise OSError(f"LoadXml → 0x{hr & 0xFFFFFFFF:08X}")

        nf = _factory(
            "Windows.UI.Notifications.ToastNotification",
            [0x20,0x4B,0x12,0x04,0xC6,0x82,0x29,0x42,
             0xB1,0x09,0xFD,0x9E,0xD4,0x66,0x2B,0x53],
        )
        _Create = ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p)
        )
        toast_notif = ctypes.c_void_p(0)
        hr = _Create(_vt(nf)[6])(nf, xml_doc, ctypes.byref(toast_notif))
        if hr != 0:
            raise OSError(f"CreateToastNotification → 0x{hr & 0xFFFFFFFF:08X}")

        _Show = ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, ctypes.c_void_p
        )
        hr = _Show(_vt(notifier)[6])(notifier, toast_notif)
        if hr != 0:
            raise OSError(f"IToastNotifier::Show → 0x{hr & 0xFFFFFFFF:08X}")

        return None

    except Exception as exc:
        return str(exc)

def load_start_apps() -> list[dict[str, str]]:
    command = [
        "powershell", "-NoProfile", "-Command",
        "Get-StartApps | Sort-Object Name | Select-Object Name, AppID | ConvertTo-Json -Depth 2",
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, timeout=15,
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
        name   = str(item.get("Name",  "")).strip()
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

        if not is_supported_build():
            messagebox.showerror(
                WINDOW_TITLE,
                f"Unsupported Windows build {windows_build_number()}.\n"
                f"This tool requires Windows 10 build {BUILD_RAW_MIN} or newer.",
            )
            self.root.destroy()
            return

        self.start_apps = load_start_apps()
        self.app_lookup = {
            f"{item['Name']} [{item['AppID']}]": item for item in self.start_apps
        }

        self.app_name_var    = tk.StringVar(value=DEFAULT_APP_NAME)
        self.app_id_var      = tk.StringVar(value=DEFAULT_APP_ID)
        self.title_var       = tk.StringVar(value="Title")
        self.button1_var     = tk.StringVar()
        self.button2_var     = tk.StringVar()
        self.image1_var      = tk.StringVar()
        self.image2_var      = tk.StringVar()
        self.image_type1_var = tk.StringVar(value="No image")
        self.image_type2_var = tk.StringVar(value="No image")
        self.status_var      = tk.StringVar(value="Ready.")

        self.build_ui()

        if uses_raw_winrt():
            self.status_var.set(
                f"\u26a0 Legacy mode: Windows build {windows_build_number()}. "
                "Using raw WinRT COM \u2014 title and body only."
            )

    def build_ui(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        creator_tab = ttk.Frame(notebook, padding=12)
        about_tab   = ttk.Frame(notebook, padding=12)
        notebook.add(creator_tab, text="Notification Creator")
        notebook.add(about_tab,   text="About")

        ttk.Label(creator_tab, text=WINDOW_TITLE, font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 10)
        )

        self.add_entry_row(creator_tab, 1, "Toast source name:",  self.app_name_var)
        self.add_app_id_row(creator_tab, 2)
        self.add_entry_row(creator_tab, 3, "Notification title:", self.title_var)
        self.add_text_row(creator_tab,  4, "Notification text:")

        if not uses_raw_winrt():
            self.add_image_row(creator_tab, 5, "Image 1:", self.image1_var, self.image_type1_var)
            self.add_image_row(creator_tab, 6, "Image 2:", self.image2_var, self.image_type2_var)
            self.add_entry_row(creator_tab, 7, "Button 1:", self.button1_var)
            self.add_entry_row(creator_tab, 8, "Button 2:", self.button2_var)

        ttk.Button(
            creator_tab, text="Create notification", command=self.send_toast
        ).grid(row=9, column=0, columnspan=3, sticky="ew", pady=(12, 8))

        ttk.Label(creator_tab, textvariable=self.status_var, wraplength=680).grid(
            row=10, column=0, columnspan=3, sticky="w", pady=(4, 6)
        )
        ttk.Label(
            creator_tab,
            text=(
                "Pick a real Windows AppUserModelID from the list or type one manually. "
                f"Supported on Windows 10 build {BUILD_RAW_MIN} through Windows 11."
            ),
            wraplength=680,
        ).grid(row=11, column=0, columnspan=3, sticky="w")

        creator_tab.columnconfigure(1, weight=1)

        ttk.Label(
            about_tab,
            text=" this made my @pixxxxyll (Effan), ps this not virus 😂😂🐓🐓🤣🤣🤣🤣🤣🤣",
            wraplength=660,
        ).pack(anchor="w")

    def add_entry_row(self, parent, row, label, variable) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(parent, textvariable=variable).grid(
            row=row, column=1, columnspan=2, sticky="ew", pady=4
        )

    def add_text_row(self, parent, row, label) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=4)
        self.message_text = tk.Text(parent, height=5, width=50)
        self.message_text.insert("1.0", "Text")
        self.message_text.grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)

    def add_app_id_row(self, parent, row) -> None:
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
        self.app_id_combo.bind("<FocusOut>",           self.sync_manual_app_id)

    def add_image_row(self, parent, row, label, path_var, type_var) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)

        row_frame = ttk.Frame(parent)
        row_frame.grid(row=row, column=1, sticky="ew", pady=4)
        row_frame.columnconfigure(0, weight=1)

        ttk.Entry(row_frame, textvariable=path_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(
            row_frame, text="Browse", command=lambda: self.browse_image(path_var)
        ).grid(row=0, column=1, padx=(6, 0))

        ttk.Combobox(
            parent, textvariable=type_var, values=IMAGE_TYPE_LABELS, state="readonly"
        ).grid(row=row, column=2, sticky="ew", pady=4, padx=(8, 0))


    def browse_image(self, target_var) -> None:
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif")],
        )
        if path:
            target_var.set(path)

    def current_app_id(self) -> str:
        text  = self.app_id_var.get().strip()
        match = re.search(r"\[(.+)\]$", text)
        return match.group(1).strip() if match else text

    def sync_selected_app(self, _event=None) -> None:
        selected = self.app_lookup.get(self.app_id_var.get().strip())
        if selected:
            self.app_name_var.set(selected["Name"])
            self.app_id_var.set(selected["AppID"])

    def sync_manual_app_id(self, _event=None) -> None:
        raw = self.current_app_id()
        if not raw:
            return
        for item in self.start_apps:
            if item["AppID"] == raw:
                self.app_name_var.set(item["Name"])
                return

    def attach_images(self, toast: "Toast") -> str | None:
        label_to_key: dict[str, str] = {lbl: key for lbl, key in IMAGE_TYPE_OPTIONS}

        entries = [
            ("Image 1", self.image1_var.get().strip(), self.image_type1_var.get().strip()),
            ("Image 2", self.image2_var.get().strip(), self.image_type2_var.get().strip()),
        ]
        seen: list[str] = []
        for label, path, display_label in entries:
            if not path or display_label == "No image":
                continue
            if display_label in seen:
                return "Image 1 and Image 2 cannot use the same image type."
            abs_path = os.path.abspath(path)
            if not os.path.exists(abs_path):
                return f"{label} not found: {abs_path}"
            key = label_to_key.get(display_label, "none")
            pos = _POSITION_MAP.get(key)
            toast.AddImage(
                ToastDisplayImage.fromPath(abs_path, position=pos, altText=label)
                if pos is not None
                else ToastDisplayImage.fromPath(abs_path, altText=label)
            )
            seen.append(display_label)
        return None

    def attach_buttons(self, toast: "Toast") -> None:
        b1 = self.button1_var.get().strip()
        b2 = self.button2_var.get().strip()
        if b1:
            toast.AddAction(ToastButton(b1, arguments="action=1"))
        if b2:
            toast.AddAction(ToastButton(b2, arguments="action=2"))

    def handle_activated(self, event: "ToastActivatedEventArgs | None") -> None:
        if event and event.arguments:
            self.status_var.set(f"Toast action clicked: {event.arguments}")
        else:
            self.status_var.set("Toast clicked.")

    def show_error(self, message: str) -> None:
        self.status_var.set(message)
        messagebox.showwarning(WINDOW_TITLE, message)


    def send_toast(self) -> None:
        app_name = self.app_name_var.get().strip() or DEFAULT_APP_NAME
        app_id   = self.current_app_id()
        if not app_id:
            self.show_error("Enter a Windows AppUserModelID or choose one from the list.")
            return

        title   = self.title_var.get().strip()                   or "Title"
        message = self.message_text.get("1.0", "end-1c").strip() or "Text"
        build   = windows_build_number()

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

        if uses_raw_winrt():
            err = _raw_winrt_toast(app_id, title, message)
            if err:
                self.show_error(f"Toast failed: {err}")
            else:
                self.status_var.set(
                    f"Sent toast as '{app_name}' (build {build}, title + body only)."
                )
            return


        toaster = InteractableWindowsToaster(app_name, app_id)
        toast   = Toast()
        toast.text_fields  = [title, message]
        toast.on_activated = self.handle_activated
        toast.on_dismissed = lambda _:  self.status_var.set("Toast dismissed.")
        toast.on_failed    = lambda ev: self.status_var.set(f"Toast failed: {ev}")

        img_err = self.attach_images(toast)
        if img_err:
            self.show_error(img_err)
            return

        self.attach_buttons(toast)
        toaster.show_toast(toast)
        self.status_var.set(f"Sent toast as '{app_name}' using AppID '{app_id}'.")

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    app = ToastGeneratorApp()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
