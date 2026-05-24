from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget


class HistogramWidget(QWidget):
    """Live RGB + luminance histogram. Set data via ``set_image(bgr_uint8)``."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hist: dict[str, np.ndarray] | None = None
        self.setMinimumHeight(110)
        self.setMaximumHeight(160)

    def set_image(self, bgr: np.ndarray | None) -> None:
        if bgr is None:
            self._hist = None
        else:
            from image_editor.core.filters import histogram
            self._hist = histogram(bgr)
        self.update()

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#0B0E13"))
        if not self._hist:
            p.setPen(QColor("#5A6473"))
            p.drawText(self.rect(), Qt.AlignCenter, "No image")
            return

        w, h = self.width(), self.height()
        peak = max(int(self._hist["y"].max()), 1)
        colors = {
            "r": QColor(255, 90, 90, 170),
            "g": QColor(90, 220, 120, 170),
            "b": QColor(90, 160, 255, 170),
            "y": QColor(220, 220, 220, 90),
        }
        for key in ("y", "r", "g", "b"):
            data = self._hist[key]
            path = QPainterPath()
            path.moveTo(0, h)
            for i in range(256):
                x = i / 255.0 * w
                y = h - (data[i] / peak) * (h - 4)
                path.lineTo(x, y)
            path.lineTo(w, h)
            path.closeSubpath()
            p.fillPath(path, colors[key])
