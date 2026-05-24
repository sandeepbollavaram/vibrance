from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from image_editor.config import SUPPORTED_EXTS


class DropZone(QFrame):
    """Empty-state widget shown when no image is loaded. Accepts drag-and-drop
    of image files and emits ``fileDropped(path)``. Also exposes an Open button
    via ``openRequested``."""

    fileDropped = Signal(str)
    openRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(280)

        v = QVBoxLayout(self)
        v.setContentsMargins(40, 40, 40, 40)
        v.setSpacing(10)
        v.setAlignment(Qt.AlignCenter)

        # A simple SVG-like ASCII glyph drawn via label icon would be brittle;
        # use a plain label with the V brand mark instead — text-only is safe.
        glyph = QLabel("V")
        glyph.setAlignment(Qt.AlignCenter)
        glyph.setStyleSheet(
            "color:#5AB0FF; font-size:54px; font-weight:800;"
            " letter-spacing:-0.04em; padding-bottom:6px;"
        )
        v.addWidget(glyph)

        title = QLabel("Drag & drop an image here")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#FFFFFF; font-size:18px; font-weight:600;")
        v.addWidget(title)

        sub = QLabel("or click Open to choose a file")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color:#9CA3AF; font-size:13px;")
        v.addWidget(sub)

        v.addSpacing(8)
        self.btn_open = QPushButton("Open Image…")
        self.btn_open.setObjectName("Primary")
        self.btn_open.setFixedWidth(180)
        self.btn_open.clicked.connect(self.openRequested)
        row = QVBoxLayout()
        row.setAlignment(Qt.AlignCenter)
        row.addWidget(self.btn_open, 0, Qt.AlignCenter)
        v.addLayout(row)

        formats = QLabel("PNG · JPG · JPEG · WEBP · BMP · TIFF")
        formats.setAlignment(Qt.AlignCenter)
        formats.setProperty("role", "caption")
        v.addSpacing(6)
        v.addWidget(formats)

    # --- drag and drop ---
    def _accept(self, urls) -> bool:
        for u in urls:
            p = Path(u.toLocalFile())
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
                return True
        return False

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:   # noqa: N802
        if e.mimeData().hasUrls() and self._accept(e.mimeData().urls()):
            self.setObjectName("DropZoneActive")
            self._refresh_style()
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragLeaveEvent(self, e: QDragLeaveEvent) -> None:   # noqa: N802
        self.setObjectName("DropZone")
        self._refresh_style()

    def dropEvent(self, e: QDropEvent) -> None:   # noqa: N802
        self.setObjectName("DropZone")
        self._refresh_style()
        for u in e.mimeData().urls():
            p = Path(u.toLocalFile())
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
                self.fileDropped.emit(str(p))
                e.acceptProposedAction()
                return
        e.ignore()

    def _refresh_style(self) -> None:
        """Re-apply stylesheet so the objectName change re-targets the QSS."""
        self.style().unpolish(self)
        self.style().polish(self)
