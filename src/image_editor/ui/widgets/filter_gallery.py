from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from image_editor.config import EditParams


def _bgr_to_pixmap(bgr) -> QPixmap:
    import cv2

    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(img)


# Curated, named looks. Each is a partial EditParams override.
PRESETS: list[tuple[str, dict]] = [
    ("Original", {}),
    ("Vivid", {"saturation": 22, "vibrance": 18, "contrast": 12}),
    ("B&W", {"saturation": -100, "contrast": 14}),
    ("Sepia", {"saturation": -100, "temperature": 30, "tint": 10, "contrast": 8}),
    ("Cool Film", {"temperature": -25, "tint": -5, "shadows": 10, "contrast": 8}),
    ("Warm Glow", {"temperature": 30, "tint": 8, "highlights": -10, "saturation": 10}),
    (
        "Cinema",
        {"contrast": 18, "highlights": -18, "shadows": 14, "saturation": -8, "temperature": -10},
    ),
    ("Polaroid", {"contrast": -8, "saturation": -15, "tint": 8, "vignette": 28}),
    ("Punch", {"contrast": 26, "saturation": 26, "vibrance": 20, "sharpen": 25}),
    ("Faded", {"contrast": -18, "saturation": -22, "shadows": 18, "highlights": -8}),
    ("Noir", {"saturation": -100, "contrast": 30, "vignette": 40, "grain": 22}),
    ("Sunset", {"temperature": 45, "tint": 10, "saturation": 15, "vignette": 14}),
]


class FilterGallery(QFrame):
    """Grid of preset thumbnails. Click one to apply its EditParams overrides."""

    presetChosen = Signal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelDeep")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 12)
        outer.setSpacing(6)

        title = QLabel("FILTERS")
        title.setObjectName("H2")
        outer.addWidget(title)

        self._scroll = QScrollArea()
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setWidgetResizable(True)
        host = QWidget()
        self._grid = QGridLayout(host)
        self._grid.setContentsMargins(0, 0, 6, 0)
        self._grid.setHorizontalSpacing(8)
        self._grid.setVerticalSpacing(10)

        self._buttons: list[QPushButton] = []
        for i, (name, _) in enumerate(PRESETS):
            btn = QPushButton(name)
            btn.setObjectName("Ghost")
            btn.setFixedSize(QSize(96, 76))
            btn.setIconSize(QSize(80, 50))
            btn.clicked.connect(lambda _c, n=name: self._on_click(n))
            self._buttons.append(btn)
            self._grid.addWidget(btn, i // 2, i % 2)
        outer.addWidget(self._scroll)
        self._scroll.setWidget(host)

    def _on_click(self, name: str) -> None:
        overrides = next((p for n, p in PRESETS if n == name), {})
        self.presetChosen.emit(name, overrides)

    def refresh_thumbnails(self, source_bgr) -> None:
        """Re-render every preset thumbnail using ``source_bgr`` as input."""
        if source_bgr is None:
            return
        import cv2

        from image_editor.core.filters import apply_all

        # Down-scale once for speed.
        h, w = source_bgr.shape[:2]
        scale = 120 / max(h, w)
        if scale < 1.0:
            thumb_src = cv2.resize(
                source_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA
            )
        else:
            thumb_src = source_bgr
        for btn, (_name, overrides) in zip(self._buttons, PRESETS, strict=False):
            params = replace(EditParams(), **overrides) if overrides else EditParams()
            try:
                rendered = apply_all(thumb_src, params)
            except Exception:
                rendered = thumb_src
            pix = _bgr_to_pixmap(rendered).scaled(
                80, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            from PySide6.QtGui import QIcon

            btn.setIcon(QIcon(pix))
