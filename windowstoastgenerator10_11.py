"""
ToastGeneratorReal
==========================================
Buy me a big mac
"""

import ctypes
import json
import os
import re
import subprocess
import sys
import tempfile

from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal, QUrl
from PyQt5.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter, QPen, QBrush, QPixmap, QCursor, QIcon, QDesktopServices
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog,
    QTabWidget, QStatusBar,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QRadioButton, QButtonGroup, QPushButton, QFileDialog,
    QMessageBox, QFrame, QGroupBox, QSizePolicy,
)

def resources_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


BUILD_MIN = 10240

def _windows_build() -> int:
    return sys.getwindowsversion().build

def _check_build() -> None:
    b = _windows_build()
    if b < BUILD_MIN:
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None, "Unsupported OS",
            f"Unsupported Windows build {b}.\n"
            f"ToastGeneratorReal requires build {BUILD_MIN} or newer.",
        )
        sys.exit(1)

try:
    from windows_toasts import (
        InteractableWindowsToaster, Toast, ToastActivatedEventArgs,
        ToastButton, ToastDisplayImage, ToastImagePosition, ToastInputTextBox,
    )
    _POS = {
        "Inline":  ToastImagePosition.Inline,
        "Hero":    ToastImagePosition.Hero,
        "AppLogo": ToastImagePosition.AppLogo,
    }
except Exception as _e:
    raise SystemExit(
        f"windows-toasts not available: {_e}\npip install windows-toasts"
    ) from _e


DEFAULT_APP_NAME = "Command Prompt"
DEFAULT_APP_ID   = r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\cmd.exe"
WINDOW_TITLE     = "ToastGeneratorReal"

IMAGE_TYPE_OPTIONS = [
    ("No image",     "none"),
    ("Inline image", "Inline"),
    ("Hero image",   "Hero"),
    ("App logo",     "AppLogo"),
]
IMAGE_TYPE_LABELS = [lbl for lbl, _ in IMAGE_TYPE_OPTIONS]


HERO_W     = 364
HERO_H     = 180
HERO_RATIO = HERO_W / HERO_H

TOAST_PRESETS = {
    "Custom (no preset)": {},
    " Mail": {
        "title": "Kasane Teto",
        "body":  "Yo twin its teto lets collab",
        "btn1":  "Reply",
        "btn2":  "Mark as read",
    },
    "Alarm": {
        "title": "cze phonk time",
        "body":  "Rise and shine",
        "btn1":  "Dismiss",
        "btn2":  "Snooze 10 min",
    },
    " System Alert": {
        "title": "albania virus",
        "body":  "we are deleting system32",
        "btn1":  "okay",
        "btn2":  "burger",
    },
    "Calendar Event": {
        "title": "CzE phonk release in 15 mins",
        "body":  "be there early",
        "btn1":  "Join",
        "btn2":  "Snooze",
    },
}

WIN2K_QSS = """
QWidget {
    font-family: "Tahoma", "Arial";
    font-size: 11px;
    color: #000000;
    background-color: #D4D0C8;
}

QMainWindow, QDialog {
    background-color: #D4D0C8;
}

QTabWidget::pane {
    border: 2px solid;
    border-color: #FFFFFF #808080 #808080 #FFFFFF;
    background-color: #D4D0C8;
    top: -1px;
}
QTabBar::tab {
    background-color: #C8C4BC;
    color: #000000;
    border: 2px solid;
    border-color: #FFFFFF #808080 #808080 #FFFFFF;
    padding: 3px 12px;
    margin-right: 2px;
    font-family: "Tahoma", "Arial";
    font-size: 11px;
}
QTabBar::tab:selected {
    background-color: #D4D0C8;
    font-weight: bold;
    border-bottom: 1px solid #D4D0C8;
    padding-bottom: 4px;
}
QTabBar::tab:hover:!selected {
    background-color: #DDD9D0;
}

QScrollArea {
    border: none;
    background-color: #D4D0C8;
}
QScrollBar:vertical {
    background: #D4D0C8;
    width: 17px;
    border: 1px solid #808080;
}
QScrollBar::handle:vertical {
    background-color: #C8C4BC;
    border: 2px solid;
    border-color: #FFFFFF #808080 #808080 #FFFFFF;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background-color: #D8D4CC;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: #D4D0C8;
    height: 17px;
    border: 2px solid;
    border-color: #FFFFFF #808080 #808080 #FFFFFF;
    subcontrol-origin: margin;
}

QGroupBox {
    border: 2px solid;
    border-color: #808080 #FFFFFF #FFFFFF #808080;
    background-color: #D4D0C8;
    margin-top: 0px;
    padding: 8px 6px 6px 6px;
    font-family: "Tahoma", "Arial";
    font-size: 11px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    background-color: #D4D0C8;
}

QLabel {
    background: transparent;
    color: #000000;
    font-family: "Tahoma", "Arial";
    font-size: 11px;
}

QLineEdit {
    background-color: #FFFFFF;
    color: #000000;
    border: 2px solid;
    border-color: #808080 #DFDFDF #DFDFDF #808080;
    padding: 1px 3px;
    font-family: "Tahoma", "Arial";
    font-size: 11px;
    selection-background-color: #000080;
    selection-color: #FFFFFF;
}
QLineEdit:focus {
    border-color: #000080 #DFDFDF #DFDFDF #000080;
}
QLineEdit:disabled {
    background-color: #D4D0C8;
    color: #808080;
}

QTextEdit {
    background-color: #FFFFFF;
    color: #000000;
    border: 2px solid;
    border-color: #808080 #DFDFDF #DFDFDF #808080;
    padding: 2px;
    font-family: "Tahoma", "Arial";
    font-size: 11px;
    selection-background-color: #000080;
    selection-color: #FFFFFF;
}
QTextEdit:focus {
    border-color: #000080 #DFDFDF #DFDFDF #000080;
}

QComboBox {
    background-color: #FFFFFF;
    color: #000000;
    border: 2px solid;
    border-color: #808080 #DFDFDF #DFDFDF #808080;
    padding: 1px 3px;
    min-height: 20px;
    font-family: "Tahoma", "Arial";
    font-size: 11px;
    selection-background-color: #000080;
    selection-color: #FFFFFF;
}
QComboBox::drop-down {
    width: 17px;
    border-left: 2px solid;
    border-color: #808080 #DFDFDF #DFDFDF #808080;
    background-color: #D4D0C8;
}
QComboBox::drop-down:hover {
    background-color: #C0BCBA;
}
QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #000000;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #000000;
    border: 2px solid #808080;
    selection-background-color: #000080;
    selection-color: #FFFFFF;
    font-family: "Tahoma", "Arial";
    font-size: 11px;
}

QPushButton {
    background-color: #D4D0C8;
    color: #000000;
    border: 2px solid;
    border-color: #FFFFFF #808080 #808080 #FFFFFF;
    outline: 1px solid #D4D0C8;
    padding: 3px 12px;
    min-height: 21px;
    min-width: 70px;
    font-family: "Tahoma", "Arial";
    font-size: 11px;
}
QPushButton:hover {
    background-color: #E0DCD0;
}
QPushButton:pressed {
    border-color: #808080 #FFFFFF #FFFFFF #808080;
    padding-top: 4px;
    padding-left: 13px;
}
QPushButton:focus {
    outline: 1px dotted #000000;
}
QPushButton:disabled {
    color: #808080;
    border-color: #DFDFDF #808080 #808080 #DFDFDF;
}

QPushButton#send_btn {
    background-color: #D4D0C8;
    color: #000000;
    border: 2px solid;
    border-color: #FFFFFF #808080 #808080 #FFFFFF;
    font-weight: bold;
    font-size: 12px;
    min-height: 26px;
    min-width: 200px;
    padding: 4px 28px;
}
QPushButton#send_btn:hover {
    background-color: #E0DCD0;
}
QPushButton#send_btn:pressed {
    border-color: #808080 #FFFFFF #FFFFFF #808080;
    padding-top: 5px;
    padding-left: 29px;
}

/* Link buttons */
QPushButton#link_btn {
    background-color: #D4D0C8;
    border: 2px solid;
    border-color: #FFFFFF #808080 #808080 #FFFFFF;
    min-height: 22px;
    min-width: 90px;
    padding: 3px 10px;
    font-family: "Tahoma", "Arial";
    font-size: 11px;
}
QPushButton#link_btn:hover {
    background-color: #E0DCD0;
}
QPushButton#link_btn:pressed {
    border-color: #808080 #FFFFFF #FFFFFF #808080;
}

/* ── CheckBox ── */
QCheckBox {
    spacing: 5px;
    background: transparent;
    font-family: "Tahoma", "Arial";
    font-size: 11px;
}
QCheckBox::indicator {
    width: 13px;
    height: 13px;
    border: 2px solid;
    border-color: #808080 #DFDFDF #DFDFDF #808080;
    background-color: #FFFFFF;
}
QCheckBox::indicator:hover {
    background-color: #F0EFEA;
}
QCheckBox::indicator:checked {
    background-color: #000080;
    border-color: #404040 #DFDFDF #DFDFDF #404040;
}
QCheckBox:disabled { color: #808080; }

/* ── RadioButton ── */
QRadioButton {
    spacing: 5px;
    background: transparent;
    font-family: "Tahoma", "Arial";
    font-size: 11px;
}
QRadioButton::indicator {
    width: 13px;
    height: 13px;
    border: 2px solid;
    border-color: #808080 #DFDFDF #DFDFDF #808080;
    border-radius: 7px;
    background-color: #FFFFFF;
}
QRadioButton::indicator:checked {
    background-color: #000080;
    border-color: #404040;
}

/* ── Separator ── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    color: #808080;
    background: #808080;
}

/* ── StatusBar ── */
QStatusBar {
    background-color: #D4D0C8;
    color: #000000;
    border-top: 2px solid;
    border-color: #808080 #FFFFFF #FFFFFF #808080;
    font-family: "Tahoma", "Arial";
    font-size: 11px;
}
QStatusBar::item { border: none; }

/* ── MessageBox ── */
QMessageBox {
    background-color: #D4D0C8;
    font-family: "Tahoma", "Arial";
    font-size: 11px;
}
QMessageBox QLabel { color: #000000; }

/* ── ToolTip ── */
QToolTip {
    background-color: #FFFFE1;
    color: #000000;
    border: 1px solid #000000;
    font-family: "Tahoma", "Arial";
    font-size: 11px;
    padding: 2px 4px;
}
"""

def load_start_apps() -> list[dict]:
    cmd = [
        "powershell", "-NoProfile", "-Command",
        "Get-StartApps | Sort-Object Name | "
        "Select-Object Name, AppID | ConvertTo-Json -Depth 2",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           check=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return [{"Name": DEFAULT_APP_NAME, "AppID": DEFAULT_APP_ID}]

    payload = r.stdout.strip()
    if not payload:
        return [{"Name": DEFAULT_APP_NAME, "AppID": DEFAULT_APP_ID}]
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return [{"Name": DEFAULT_APP_NAME, "AppID": DEFAULT_APP_ID}]

    if isinstance(data, dict):
        data = [data]

    apps = [
        {"Name": str(i.get("Name", "")).strip(),
         "AppID": str(i.get("AppID", "")).strip()}
        for i in data
        if str(i.get("Name", "")).strip() and str(i.get("AppID", "")).strip()
    ]
    return apps or [{"Name": DEFAULT_APP_NAME, "AppID": DEFAULT_APP_ID}]

def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    f = lbl.font()
    f.setBold(True)
    lbl.setFont(f)
    return lbl

def _separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line

def _group(title: str = "") -> QGroupBox:
    return QGroupBox(title)

class HeroCropDialog(QDialog):
    def __init__(self, parent, image_path: str):
        super().__init__(parent)
        self.setWindowTitle("Crop Hero Image  (364 \u00d7 180)")
        self.setModal(True)
        self._out_path: str | None = None
        self._dragging = False
        self._drag_start = QPoint()
        self._box_origin = QPoint()

        img = QImage(image_path)
        if img.isNull():
            QMessageBox.critical(self, "Error", "Cannot load image.")
            self.reject()
            return

        src_w, src_h = img.width(), img.height()
        self._scale  = min(600 / src_w, 480 / src_h, 1.0)
        self._prev_w = max(1, int(src_w * self._scale))
        self._prev_h = max(1, int(src_h * self._scale))
        self._src_img = img

        bw = self._prev_w
        bh = int(bw / HERO_RATIO)
        if bh > self._prev_h:
            bh = self._prev_h
            bw = int(bh * HERO_RATIO)
        self._box = QRect(
            (self._prev_w - bw) // 2,
            (self._prev_h - bh) // 2,
            bw, bh,
            )

        scaled = img.scaled(self._prev_w, self._prev_h,
                            Qt.IgnoreAspectRatio,
                            Qt.SmoothTransformation)
        self._preview = QPixmap.fromImage(scaled)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Drag the blue rectangle to choose the hero crop region."))

        self._canvas = QWidget()
        self._canvas.setFixedSize(self._prev_w, self._prev_h)
        self._canvas.setMouseTracking(True)
        self._canvas.paintEvent      = self._paint
        self._canvas.mousePressEvent = self._mouse_down
        self._canvas.mouseReleaseEvent = self._mouse_up
        self._canvas.mouseMoveEvent  = self._mouse_move
        layout.addWidget(self._canvas)

        self._coord_lbl = QLabel()
        self._update_coord()
        layout.addWidget(self._coord_lbl)
        layout.addWidget(_separator())

        btns = QHBoxLayout()
        btns.addStretch()
        self._ok_btn = QPushButton("Crop && Send")
        self._ok_btn.clicked.connect(self._do_crop)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(self._ok_btn)
        btns.addWidget(cancel)
        layout.addLayout(btns)
        self.adjustSize()

    def _paint(self, _event):
        p = QPainter(self._canvas)
        p.drawPixmap(0, 0, self._preview)
        p.setBrush(QBrush(QColor(0, 0, 0, 110)))
        p.setPen(Qt.PenStyle.NoPen)
        b = self._box
        p.drawRect(0, 0, self._prev_w, b.y())
        p.drawRect(0, b.y() + b.height(),
                   self._prev_w, self._prev_h - b.y() - b.height())
        p.drawRect(0, b.y(), b.x(), b.height())
        p.drawRect(b.x() + b.width(), b.y(),
                   self._prev_w - b.x() - b.width(), b.height())
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(0, 120, 215), 2))
        p.drawRect(b)
        p.setBrush(QBrush(QColor(0, 120, 215)))
        p.setPen(Qt.PenStyle.NoPen)
        for cx, cy in [(b.x(), b.y()), (b.right(), b.y()),
                       (b.x(), b.bottom()), (b.right(), b.bottom())]:
            p.drawEllipse(QPoint(cx, cy), 5, 5)
        p.end()

    def _mouse_down(self, e):
        if self._box.contains(e.pos()):
            self._dragging  = True
            self._drag_start = e.pos()
            self._box_origin = self._box.topLeft()
            self._canvas.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))

    def _mouse_up(self, _e):
        self._dragging = False
        self._canvas.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def _mouse_move(self, e):
        if not self._dragging:
            cur = (Qt.CursorShape.SizeAllCursor
                   if self._box.contains(e.pos())
                   else Qt.CursorShape.ArrowCursor)
            self._canvas.setCursor(QCursor(cur))
            return
        dx = e.pos().x() - self._drag_start.x()
        dy = e.pos().y() - self._drag_start.y()
        nx = max(0, min(self._box_origin.x() + dx,
                        self._prev_w - self._box.width()))
        ny = max(0, min(self._box_origin.y() + dy,
                        self._prev_h - self._box.height()))
        self._box.moveTo(nx, ny)
        self._update_coord()
        self._canvas.update()

    def _update_coord(self):
        sx = int(self._box.x()      / self._scale)
        sy = int(self._box.y()      / self._scale)
        sw = int(self._box.width()  / self._scale)
        sh = int(self._box.height() / self._scale)
        self._coord_lbl.setText(
            f"Source crop:  x={sx}  y={sy}  {sw} \u00d7 {sh} px")

    def _do_crop(self):
        sx = max(0, min(int(self._box.x()      / self._scale),
                        self._src_img.width()  - 1))
        sy = max(0, min(int(self._box.y()      / self._scale),
                        self._src_img.height() - 1))
        sw = max(1, min(int(self._box.width()  / self._scale),
                        self._src_img.width()  - sx))
        sh = max(1, min(int(self._box.height() / self._scale),
                        self._src_img.height() - sy))

        cropped = self._src_img.copy(sx, sy, sw, sh)
        final   = cropped.scaled(HERO_W, HERO_H,
                                 Qt.IgnoreAspectRatio,
                                 Qt.SmoothTransformation)
        fd, tmp = tempfile.mkstemp(suffix="_hero_crop.png", prefix="toastgen_")
        os.close(fd)
        final.save(tmp, "PNG")
        self._out_path = tmp
        self.accept()

    def cropped_path(self) -> str | None:
        return self._out_path


class ImageRow(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)

        row.addWidget(QLabel(label), 0)

        self.path_edit = QLineEdit()
        row.addWidget(self.path_edit, 1)

        browse = QPushButton("Browse\u2026")
        browse.setFixedWidth(80)
        browse.clicked.connect(self._browse)
        row.addWidget(browse, 0)

        self.type_combo = QComboBox()
        self.type_combo.addItems(IMAGE_TYPE_LABELS)
        self.type_combo.setFixedWidth(130)
        self.type_combo.currentTextChanged.connect(self._on_type_change)
        row.addWidget(self.type_combo, 0)

        self._shape_widget = QWidget()
        sh = QHBoxLayout(self._shape_widget)
        sh.setContentsMargins(0, 0, 0, 0)
        sh.addWidget(QLabel("Logo shape:"))
        self.rb_circle = QRadioButton("Circle")
        self.rb_square = QRadioButton("Square")
        self.rb_circle.setChecked(True)
        grp = QButtonGroup(self)
        grp.addButton(self.rb_circle)
        grp.addButton(self.rb_square)
        sh.addWidget(self.rb_circle)
        sh.addWidget(self.rb_square)
        self._shape_widget.setVisible(False)

    def shape_row_widget(self) -> QWidget:
        return self._shape_widget

    def reset(self):
        self.path_edit.clear()
        self.type_combo.setCurrentText("No image")
        self.rb_circle.setChecked(True)
        self._shape_widget.setVisible(False)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)",
        )
        if path:
            self.path_edit.setText(path)

    def _on_type_change(self, text: str):
        self._shape_widget.setVisible(text == "App logo")


class ToastFrame(QMainWindow):

    _status_signal = pyqtSignal(str)
    _reply_signal  = pyqtSignal(str)

    REPLY_ID = "toast_reply_input"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)

        self.start_apps = load_start_apps()
        self.app_lookup = {
            f"{a['Name']} [{a['AppID']}]": a for a in self.start_apps
        }

        self._status_signal.connect(self._set_status)
        self._reply_signal.connect(self._show_reply_dialog)

        self._build_ui()
        self._lock_window_size()

    def _build_ui(self):
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        creator = QWidget()
        about   = QWidget()
        tabs.addTab(creator, "  Notification Creator  ")
        tabs.addTab(about,   "  About  ")

        self._build_creator(creator)
        self._build_about(about)

        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("Ready.")

        right = QLabel(f"Build {_windows_build()}")
        right.setAlignment(Qt.AlignRight)
        self._statusbar.addPermanentWidget(right)

    def _build_creator(self, container: QWidget):
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        layout.addWidget(_section_label("Toast Type"))
        layout.addWidget(self._make_preset_box(container))

        layout.addWidget(_section_label("Toast Source"))
        layout.addWidget(self._make_source_box(container))

        layout.addWidget(_section_label("Content"))
        layout.addWidget(self._make_content_box(container))

        layout.addWidget(_section_label("Images"))
        layout.addWidget(self._make_images_box(container))

        layout.addWidget(_section_label("Action Buttons"))
        layout.addWidget(self._make_buttons_box(container))

        self.btn_send = QPushButton("Create Notification")
        self.btn_send.setObjectName("send_btn")
        f = self.btn_send.font()
        f.setBold(True)
        f.setPointSize(f.pointSize() + 1)
        self.btn_send.setFont(f)
        self.btn_send.setMinimumHeight(28)
        self.btn_send.clicked.connect(self._on_send)

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.clicked.connect(self._reset_form)

        send_row = QHBoxLayout()
        send_row.addStretch()
        send_row.addWidget(self.btn_reset)
        send_row.addWidget(self.btn_send)
        send_row.addStretch()
        layout.addLayout(send_row)
        layout.addStretch()

    def _make_preset_box(self, _parent) -> QGroupBox:
        g = _group()
        fl = QFormLayout(g)
        fl.setContentsMargins(8, 8, 8, 8)
        fl.setVerticalSpacing(4)
        fl.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.cmb_preset = QComboBox()
        self.cmb_preset.addItems(list(TOAST_PRESETS.keys()))
        self.cmb_preset.currentTextChanged.connect(self._on_preset)
        fl.addRow("Preset:", self.cmb_preset)

        self._preset_hint = QLabel("")
        self._preset_hint.setStyleSheet("color: #444488;")
        fl.addRow("", self._preset_hint)
        return g

    def _make_source_box(self, _parent) -> QGroupBox:
        g = _group()
        fl = QFormLayout(g)
        fl.setContentsMargins(8, 8, 8, 8)
        fl.setVerticalSpacing(4)
        fl.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.txt_app_name = QLineEdit(DEFAULT_APP_NAME)
        fl.addRow("Source name:", self.txt_app_name)

        self.cmb_app_id = QComboBox()
        self.cmb_app_id.setEditable(True)
        self.cmb_app_id.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        choices = [f"{a['Name']} [{a['AppID']}]" for a in self.start_apps]
        self.cmb_app_id.addItems(choices)
        self.cmb_app_id.setCurrentText(DEFAULT_APP_ID)
        self.cmb_app_id.currentTextChanged.connect(self._on_appid_changed)
        fl.addRow("AppUserModelID:", self.cmb_app_id)
        return g

    def _make_content_box(self, _parent) -> QGroupBox:
        g = _group()
        fl = QFormLayout(g)
        fl.setContentsMargins(8, 8, 8, 8)
        fl.setVerticalSpacing(4)
        fl.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.txt_title = QLineEdit("Title")
        fl.addRow("Title:", self.txt_title)

        self.txt_body = QTextEdit("Text")
        self.txt_body.setFixedHeight(60)
        fl.addRow("Body:", self.txt_body)

        return g

    def _make_images_box(self, _parent) -> QGroupBox:
        g = _group()
        vl = QVBoxLayout(g)
        vl.setContentsMargins(8, 8, 8, 8)
        vl.setSpacing(4)

        self.img_row1 = ImageRow("Image 1:")
        self.img_row2 = ImageRow("Image 2:")
        vl.addWidget(self.img_row1)
        vl.addWidget(self.img_row1.shape_row_widget())
        vl.addWidget(self.img_row2)
        vl.addWidget(self.img_row2.shape_row_widget())
        return g

    def _make_buttons_box(self, _parent) -> QGroupBox:
        g = _group()
        fl = QFormLayout(g)
        fl.setContentsMargins(8, 8, 8, 8)
        fl.setVerticalSpacing(4)
        fl.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.txt_btn1 = QLineEdit()
        self.txt_btn2 = QLineEdit()
        fl.addRow("Button 1 label:", self.txt_btn1)
        fl.addRow("Button 2 label:", self.txt_btn2)

        fl.addRow(_separator())

        self.chk_reply = QCheckBox("Enable reply text box")
        self.chk_reply.stateChanged.connect(self._on_reply_toggle)
        fl.addRow(self.chk_reply)

        self.txt_rph = QLineEdit("Write a reply\u2026")
        self.txt_rph.setEnabled(False)
        fl.addRow("Placeholder text:", self.txt_rph)

        self.txt_rdv = QLineEdit()
        self.txt_rdv.setEnabled(False)
        fl.addRow("Default reply value:", self.txt_rdv)
        return g

    def _lock_window_size(self):
        self.adjustSize()
        frame_size = self.frameSize()
        if frame_size.width() <= 0 or frame_size.height() <= 0:
            frame_size = self.sizeHint()

        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            width = min(frame_size.width(), max(760, available.width() - 80))
            height = min(frame_size.height(), max(640, available.height() - 80))
        else:
            width = frame_size.width()
            height = frame_size.height()

        self.setFixedSize(width, height)

    def _build_about(self, container: QWidget):
        vl = QVBoxLayout(container)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setSpacing(10)

        title = QLabel(WINDOW_TITLE)
        f = title.font()
        f.setPointSize(f.pointSize() + 4)
        f.setBold(True)
        title.setFont(f)
        vl.addWidget(title)

        vl.addWidget(QLabel(
            f"Windows Toast Notification Generator"))
        vl.addWidget(_separator())
        vl.addWidget(QLabel("Made by @pixxxxyll"))
        vl.addWidget(QLabel(
            "theres no virus on this trust me"))

        links = [
            ("GitHub",          "https://github.com/pixxxxyll"),
            ("YouTube",         "https://www.youtube.com/@pixxxxyll"),
            ("Discord server",  "https://discord.gg/TR9cjWcZmp"),
        ]
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        for label, url in links:
            btn = QPushButton(label)
            btn.setObjectName("link_btn")
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setFixedHeight(26)
            btn.clicked.connect(lambda _, u=url: self._open_external_link(u))
            btn_row.addWidget(btn)
        btn_row.addStretch()
        vl.addLayout(btn_row)
        vl.addWidget(_separator())

        info = [
            ("Hero image",   "Large banner at top \u2014 drag to crop before sending."),
            ("Inline image", "Thumbnail on the right side of the toast."),
            ("App logo",     "Replaces the app icon \u2014 circle or square."),
            ("Button 1/2",   "Action buttons inside the toast."),
            ("Reply box",    "Inline text field for reply-style toasts."),
        ]
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(8)
        for row, (key, desc) in enumerate(info):
            kl = QLabel(key)
            f  = kl.font(); f.setBold(True); kl.setFont(f)
            grid.addWidget(kl,           row, 0, Qt.AlignmentFlag.AlignTop)
            grid.addWidget(QLabel(desc), row, 1, Qt.AlignmentFlag.AlignTop)
        grid.setColumnStretch(1, 1)
        vl.addLayout(grid)
        vl.addStretch()

    def _set_status(self, msg: str):
        self._statusbar.showMessage(msg)

    def _open_external_link(self, url: str):
        try:
            if QDesktopServices.openUrl(QUrl(url)):
                self._set_status(f"Opened {url}")
                return
        except Exception:
            pass

        QMessageBox.warning(
            self,
            "Open link failed",
            f"Could not open this link:\n{url}",
        )
        self._set_status(f"Failed to open {url}")

    def _on_reply_toggle(self, state: int):
        on = bool(state)
        self.txt_rph.setEnabled(on)
        self.txt_rdv.setEnabled(on)

    def _on_appid_changed(self, text: str):
        m = re.search(r"\[(.+)\]$", text.strip())
        app_id = m.group(1).strip() if m else text.strip()
        item = self.app_lookup.get(text.strip())
        if item:
            self.txt_app_name.setText(item["Name"])
        else:
            for a in self.start_apps:
                if a["AppID"] == app_id:
                    self.txt_app_name.setText(a["Name"])
                    break

    def _on_preset(self, text: str):
        p = TOAST_PRESETS.get(text, {})
        if not p:
            self._preset_hint.setText("")
            return
        self.txt_title.setText(p.get("title", ""))
        self.txt_body.setPlainText(p.get("body", ""))
        self.txt_btn1.setText(p.get("btn1", ""))
        self.txt_btn2.setText(p.get("btn2", ""))
        self._preset_hint.setText(
            "Filled in: title, body, and buttons.  You can still edit any field.")

    def _on_send(self):
        self.send_toast()

    def _reset_form(self):
        self.cmb_preset.setCurrentIndex(0)
        self._preset_hint.setText("")

        self.txt_app_name.setText(DEFAULT_APP_NAME)
        self.cmb_app_id.setCurrentText(DEFAULT_APP_ID)
        self.txt_title.setText("Title")
        self.txt_body.setPlainText("Text")
        self.img_row1.reset()
        self.img_row2.reset()

        self.txt_btn1.clear()
        self.txt_btn2.clear()
        self.chk_reply.setChecked(False)
        self.txt_rph.setText("Write a reply…")
        self.txt_rdv.clear()

        self._set_status("Form reset.")

    def _current_app_id(self) -> str:
        text = self.cmb_app_id.currentText().strip()
        m = re.search(r"\[(.+)\]$", text)
        return m.group(1).strip() if m else text

    def _crop_hero(self, path: str) -> str | None:
        dlg = HeroCropDialog(self, path)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg.cropped_path()
        return None

    def _attach_images(self, toast: Toast) -> str | None:
        l2k = {lbl: key for lbl, key in IMAGE_TYPE_OPTIONS}
        rows = [("Image 1", self.img_row1), ("Image 2", self.img_row2)]
        seen = []
        for lbl, row in rows:
            path = row.path_edit.text().strip()
            dlbl = row.type_combo.currentText()
            if not path or dlbl == "No image":
                continue
            if dlbl in seen:
                return "Image 1 and Image 2 cannot use the same image type."
            ap = os.path.abspath(path)
            if not os.path.exists(ap):
                return f"{lbl} not found: {ap}"

            key = l2k.get(dlbl, "none")
            pos = _POS.get(key)

            if key == "Hero":
                cropped = self._crop_hero(ap)
                if cropped is None:
                    return None
                ap = cropped

            cc = row.rb_circle.isChecked() if key == "AppLogo" else None

            if pos is not None:
                obj = (
                    ToastDisplayImage.fromPath(ap, position=pos, circleCrop=cc, altText=lbl)
                    if cc is not None
                    else ToastDisplayImage.fromPath(ap, position=pos, altText=lbl)
                )
            else:
                obj = ToastDisplayImage.fromPath(ap, altText=lbl)

            toast.AddImage(obj)
            seen.append(dlbl)
        return None

    def _attach_buttons(self, toast: Toast):
        b1 = self.txt_btn1.text().strip()
        b2 = self.txt_btn2.text().strip()

        if self.chk_reply.isChecked():
            ph = self.txt_rph.text().strip() or "Write a reply\u2026"
            dv = self.txt_rdv.text().strip()
            toast.AddInput(ToastInputTextBox(self.REPLY_ID, ph, dv))

        if b1:
            toast.AddAction(ToastButton(b1, arguments="action=1"))
        if b2:
            toast.AddAction(ToastButton(b2, arguments="action=2"))

    def send_toast(self):
        app_name = self.txt_app_name.text().strip() or DEFAULT_APP_NAME
        app_id   = self._current_app_id()
        if not app_id:
            QMessageBox.warning(self, WINDOW_TITLE,
                                "Enter a Windows AppUserModelID "
                                "or choose one from the list.")
            return

        title   = self.txt_title.text().strip()       or "Title"
        message = self.txt_body.toPlainText().strip()  or "Text"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

        toaster = InteractableWindowsToaster(app_name, app_id)
        toast   = Toast()
        toast.text_fields  = [title, message]
        toast.on_activated = self._handle_activated
        toast.on_dismissed = lambda _: self._status_signal.emit("Toast dismissed.")
        toast.on_failed    = lambda ev: self._status_signal.emit(f"Toast failed: {ev}")

        err = self._attach_images(toast)
        if err:
            QMessageBox.warning(self, WINDOW_TITLE, err)
            self._set_status(f"Error: {err}")
            return

        self._attach_buttons(toast)
        toaster.show_toast(toast)
        self._set_status(f"Sent as '{app_name}'  [{app_id}]")

    def _handle_activated(self, event):
        if event is None:
            self._status_signal.emit("Toast clicked.")
            return
        reply = None
        if hasattr(event, "inputs") and event.inputs:
            reply = event.inputs.get(self.REPLY_ID, "").strip()
        if reply:
            self._reply_signal.emit(reply)
        elif event.arguments:
            self._status_signal.emit(f"Action clicked: {event.arguments}")
        else:
            self._status_signal.emit("Toast clicked.")

    def _show_reply_dialog(self, text: str):
        dlg = QDialog(self)
        dlg.setWindowTitle("Reply received")
        dlg.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        dlg.setMinimumWidth(340)
        vl = QVBoxLayout(dlg)

        vl.addWidget(QLabel("Reply:"))
        te = QTextEdit(text)
        te.setReadOnly(True)
        te.setFixedHeight(80)
        vl.addWidget(te)

        br = QHBoxLayout()
        br.addStretch()
        copy_btn  = QPushButton("Copy")
        close_btn = QPushButton("Close")

        def _copy():
            QApplication.clipboard().setText(text)
            copy_btn.setText("Copied!")

        copy_btn.clicked.connect(_copy)
        close_btn.clicked.connect(dlg.accept)
        br.addWidget(copy_btn)
        br.addWidget(close_btn)
        vl.addLayout(br)

        dlg.show()
        self._set_status(
            f"Reply: {text[:60]}" + ("\u2026" if len(text) > 60 else ""))

def main() -> int:
    _check_build()
    app = QApplication(sys.argv)
    app.setStyleSheet(WIN2K_QSS)

    icon = QIcon(resources_path("toast.ico"))
    app.setWindowIcon(icon)

    frame = ToastFrame()
    frame.setWindowIcon(icon)
    frame.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
