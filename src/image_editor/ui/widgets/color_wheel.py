from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRect, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QMouseEvent,
    QPainter,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class ColorWheel(QWidget):
    """A single 3-way color-grading wheel.

    Internally stores a puck position as ``(dx, dy)`` in ``-1..1`` normalized
    coords (clamped to the unit disk). The wheel itself is just a HSV ring; the
    puck represents the offset that callers feed into ``filters.color_grade``.
    """

    valueChanged = Signal(float, float)  # dx, dy

    MAX_RADIUS = 0.5  # UI cap — large grades look ugly

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(112, 112)
        self.setMouseTracking(True)
        self._dx = 0.0
        self._dy = 0.0
        self._dragging = False

    def value(self) -> tuple[float, float]:
        return self._dx, self._dy

    def set_value(self, dx: float, dy: float) -> None:
        self._dx, self._dy = self._clamp(dx, dy)
        self.update()

    def reset(self) -> None:
        self._dx = self._dy = 0.0
        self.update()
        self.valueChanged.emit(0.0, 0.0)

    def _clamp(self, dx: float, dy: float) -> tuple[float, float]:
        r = math.hypot(dx, dy)
        cap = self.MAX_RADIUS
        if r > cap:
            dx *= cap / r
            dy *= cap / r
        return dx, dy

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = min(self.width(), self.height())
        rect = QRect((self.width() - s) // 2, (self.height() - s) // 2, s, s)
        cx, cy = rect.center().x(), rect.center().y()
        r = s / 2 - 2

        # Outer hue ring (conical gradient)
        ring = QConicalGradient(cx, cy, 90)
        for i in range(0, 360, 30):
            ring.setColorAt(i / 360.0, QColor.fromHsvF(i / 360.0, 0.95, 1.0))
        p.setBrush(QBrush(ring))
        p.setPen(Qt.NoPen)
        p.drawEllipse(rect)

        # Inner radial vignette (toward white center)
        rad = QRadialGradient(cx, cy, r)
        rad.setColorAt(0.0, QColor(255, 255, 255, 230))
        rad.setColorAt(0.7, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(rad))
        p.drawEllipse(rect)

        # Dark hole
        inner = QRect(rect.x() + s // 4, rect.y() + s // 4, s // 2, s // 2)
        p.setBrush(QColor(10, 14, 26, 255))
        p.drawEllipse(inner)

        # Puck
        px = cx + self._dx * r
        py = cy + self._dy * r
        p.setBrush(QColor(255, 255, 255, 240))
        p.setPen(QPen(QColor(90, 176, 255, 255), 2))
        p.drawEllipse(QPointF(px, py), 6, 6)

        # Cross-hair guide
        guide = QPen(QColor(255, 255, 255, 28), 1)
        p.setPen(guide)
        p.drawLine(rect.left() + 6, cy, rect.right() - 6, cy)
        p.drawLine(cx, rect.top() + 6, cx, rect.bottom() - 6)

    def mousePressEvent(self, event: QMouseEvent):  # noqa: N802
        self._dragging = True
        self._update_from_point(event.position())

    def mouseMoveEvent(self, event: QMouseEvent):  # noqa: N802
        if self._dragging:
            self._update_from_point(event.position())

    def mouseReleaseEvent(self, event):  # noqa: N802
        self._dragging = False

    def mouseDoubleClickEvent(self, event):  # noqa: N802
        self.reset()

    def _update_from_point(self, pt: QPointF) -> None:
        s = min(self.width(), self.height())
        r = s / 2 - 2
        cx, cy = self.width() / 2, self.height() / 2
        dx = (pt.x() - cx) / r
        dy = (pt.y() - cy) / r
        self._dx, self._dy = self._clamp(dx, dy)
        self.update()
        self.valueChanged.emit(self._dx, self._dy)


class ColorWheelTriad(QFrame):
    """Three labeled wheels (Shadows / Midtones / Highlights) arranged in a row."""

    valuesChanged = Signal(tuple, tuple, tuple)  # sh, mid, hi (each dx,dy)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelDeep")

        v = QVBoxLayout(self)
        v.setContentsMargins(12, 10, 12, 12)
        v.setSpacing(6)

        title = QLabel("COLOR GRADING")
        title.setObjectName("H2")
        v.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(6)
        self.sh = ColorWheel()
        self.mid = ColorWheel()
        self.hi = ColorWheel()
        for wheel, label in [(self.sh, "Shadows"), (self.mid, "Midtones"), (self.hi, "Highlights")]:
            col = QVBoxLayout()
            col.setSpacing(2)
            col.addWidget(wheel, 0, Qt.AlignCenter)
            cap = QLabel(label)
            cap.setAlignment(Qt.AlignCenter)
            cap.setProperty("role", "caption")
            col.addWidget(cap)
            row.addLayout(col)
        v.addLayout(row)

        for w in (self.sh, self.mid, self.hi):
            w.valueChanged.connect(self._emit)

    def _emit(self, *_) -> None:
        self.valuesChanged.emit(self.sh.value(), self.mid.value(), self.hi.value())

    def reset(self) -> None:
        self.sh.set_value(0, 0)
        self.mid.set_value(0, 0)
        self.hi.set_value(0, 0)
        self._emit()
