from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class _CurveCanvas(QWidget):
    """A small interactive RGB curve editor with draggable points."""

    curveChanged = Signal(list)  # list[(x, y)] in 0..1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(180)
        self.setMinimumWidth(220)
        self._points: list[list[float]] = [[0.0, 0.0], [1.0, 1.0]]
        self._dragging: int | None = None

    def points(self) -> list[tuple[float, float]]:
        return [(p[0], p[1]) for p in self._points]

    def set_points(self, pts: list[tuple[float, float]] | None) -> None:
        if not pts or len(pts) < 2:
            self._points = [[0.0, 0.0], [1.0, 1.0]]
        else:
            self._points = sorted([list(p) for p in pts], key=lambda p: p[0])
        self.update()
        self.curveChanged.emit(self.points())

    def reset(self) -> None:
        self.set_points(None)

    # ------- geometry helpers -------
    def _w(self) -> int:
        return max(self.width() - 16, 1)

    def _h(self) -> int:
        return max(self.height() - 16, 1)

    def _to_px(self, p: list[float]) -> QPointF:
        return QPointF(8 + p[0] * self._w(), 8 + (1.0 - p[1]) * self._h())

    def _from_px(self, x: float, y: float) -> tuple[float, float]:
        nx = max(0.0, min(1.0, (x - 8) / self._w()))
        ny = max(0.0, min(1.0, 1.0 - (y - 8) / self._h()))
        return nx, ny

    # ------- painting -------
    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(8, 12, 22, 220))

        # Grid
        grid = QPen(QColor(255, 255, 255, 22), 1)
        p.setPen(grid)
        for i in range(1, 4):
            x = 8 + self._w() * i / 4
            y = 8 + self._h() * i / 4
            p.drawLine(QPointF(x, 8), QPointF(x, 8 + self._h()))
            p.drawLine(QPointF(8, y), QPointF(8 + self._w(), y))

        # Diagonal reference
        ref = QPen(QColor(90, 176, 255, 60), 1, Qt.DashLine)
        p.setPen(ref)
        p.drawLine(self._to_px([0.0, 0.0]), self._to_px([1.0, 1.0]))

        # Curve (piecewise linear; visually fine for RGB curves)
        curve = QPen(QColor(90, 176, 255, 255), 2)
        p.setPen(curve)
        pts = sorted(self._points, key=lambda q: q[0])
        for i in range(len(pts) - 1):
            p.drawLine(self._to_px(pts[i]), self._to_px(pts[i + 1]))

        # Control points
        for pt in pts:
            center = self._to_px(pt)
            p.setBrush(QColor(255, 255, 255, 240))
            p.setPen(QPen(QColor(90, 176, 255, 255), 2))
            p.drawEllipse(center, 5, 5)

    # ------- interaction -------
    def mousePressEvent(self, event: QMouseEvent):  # noqa: N802
        idx = self._hit_test(event.position())
        if idx is not None:
            self._dragging = idx
            if event.button() == Qt.RightButton and 0 < idx < len(self._points) - 1:
                # Right-click on an interior point removes it.
                self._points.pop(idx)
                self._dragging = None
                self.update()
                self.curveChanged.emit(self.points())
        else:
            nx, ny = self._from_px(event.position().x(), event.position().y())
            self._points.append([nx, ny])
            self._points.sort(key=lambda q: q[0])
            self._dragging = self._points.index([nx, ny])
            self.update()
            self.curveChanged.emit(self.points())

    def mouseMoveEvent(self, event: QMouseEvent):  # noqa: N802
        if self._dragging is None:
            return
        nx, ny = self._from_px(event.position().x(), event.position().y())
        # Endpoints stay locked horizontally
        if self._dragging == 0:
            nx = 0.0
        elif self._dragging == len(self._points) - 1:
            nx = 1.0
        # Keep order: don't drag past neighbors
        left = self._points[self._dragging - 1][0] if self._dragging > 0 else 0.0
        right = (
            self._points[self._dragging + 1][0] if self._dragging < len(self._points) - 1 else 1.0
        )
        nx = max(left + 0.001, min(right - 0.001, nx))
        self._points[self._dragging] = [nx, ny]
        self.update()
        self.curveChanged.emit(self.points())

    def mouseReleaseEvent(self, event):  # noqa: N802
        self._dragging = None

    def _hit_test(self, pt: QPointF) -> int | None:
        for i, p in enumerate(self._points):
            if (self._to_px(p) - pt).manhattanLength() < 10:
                return i
        return None


class CurvesEditor(QFrame):
    """RGB curves editor card with header + reset button."""

    curveChanged = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelDeep")

        v = QVBoxLayout(self)
        v.setContentsMargins(12, 10, 12, 12)
        v.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel("CURVES")
        title.setObjectName("H2")
        reset = QPushButton("Reset")
        reset.setObjectName("Ghost")
        reset.setFixedHeight(26)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(reset)
        v.addLayout(header)

        self._canvas = _CurveCanvas()
        v.addWidget(self._canvas)

        hint = QLabel(
            "Click empty area to add a point · right-click an interior point to remove · drag to shape"
        )
        hint.setProperty("role", "caption")
        hint.setWordWrap(True)
        v.addWidget(hint)

        self._canvas.curveChanged.connect(self.curveChanged)
        reset.clicked.connect(self._canvas.reset)

    def points(self) -> list[tuple[float, float]]:
        return self._canvas.points()

    def set_points(self, pts: list[tuple[float, float]] | None) -> None:
        self._canvas.set_points(pts)
