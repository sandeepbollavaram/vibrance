from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QFont, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class SplitCompareWidget(QWidget):
    """Draggable vertical split between two pixmaps with 'Before'/'After' labels."""

    def __init__(self, before: QPixmap, after: QPixmap, parent=None):
        super().__init__(parent)
        self._before = before
        self._after = after
        self._pos = 0.5
        self._dragging = False
        self.setMinimumSize(1000, 600)
        self.setMouseTracking(True)
        self.setCursor(Qt.SplitHCursor)

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        w, h = self.width(), self.height()
        before = self._before.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        after = self._after.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        bx = (w - before.width()) // 2
        by = (h - before.height()) // 2

        # Backdrop
        p.fillRect(self.rect(), Qt.black)

        # After (full)
        p.drawPixmap(bx, by, after)
        # Before (clipped)
        split_x = int(w * self._pos)
        p.save()
        p.setClipRect(0, 0, split_x, h)
        p.drawPixmap(bx, by, before)
        p.restore()

        # Divider
        pen = QPen()
        pen.setColor(Qt.white)
        pen.setWidth(2)
        p.setPen(pen)
        p.drawLine(split_x, 0, split_x, h)

        # Handle dot
        p.setBrush(Qt.white)
        p.drawEllipse(QPoint(split_x, h // 2), 9, 9)

        # Labels
        p.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        p.setPen(Qt.white)
        p.fillRect(10, 10, 70, 22, Qt.black)
        p.drawText(18, 26, "BEFORE")
        p.fillRect(w - 80, 10, 70, 22, Qt.black)
        p.drawText(w - 72, 26, "AFTER")

    def mousePressEvent(self, event: QMouseEvent):  # noqa: N802
        self._dragging = True
        self._set_pos(event.position().x())

    def mouseReleaseEvent(self, event):  # noqa: N802
        self._dragging = False

    def mouseMoveEvent(self, event: QMouseEvent):  # noqa: N802
        if self._dragging:
            self._set_pos(event.position().x())

    def _set_pos(self, x: float) -> None:
        self._pos = max(0.0, min(1.0, x / max(self.width(), 1)))
        self.update()
