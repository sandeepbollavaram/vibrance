from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
)


class _CropCanvas(QLabel):
    rectChanged = Signal(QRect)

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self._source = pixmap
        self._scaled = pixmap
        self._origin: QPoint | None = None
        self._rect = QRect()
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(640, 480)
        self.setMouseTracking(True)

    def resizeEvent(self, event):  # noqa: N802
        self._scaled = self._source.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.setPixmap(self._scaled)
        super().resizeEvent(event)

    def mousePressEvent(self, event: QMouseEvent):  # noqa: N802
        self._origin = event.position().toPoint()
        self._rect = QRect(self._origin, self._origin)
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):  # noqa: N802
        if self._origin is None:
            return
        self._rect = QRect(self._origin, event.position().toPoint()).normalized()
        self.update()

    def mouseReleaseEvent(self, event):  # noqa: N802
        self.rectChanged.emit(self._rect)

    def paintEvent(self, event):  # noqa: N802
        super().paintEvent(event)
        if self._rect.isNull():
            return
        p = QPainter(self)
        pen = QPen(Qt.white, 2, Qt.DashLine)
        p.setPen(pen)
        p.drawRect(self._rect)

    def source_rect(self) -> QRect | None:
        """Map the on-screen selection back to source-pixmap coordinates."""
        if self._rect.isNull() or self._scaled.isNull():
            return None
        # offset of scaled pixmap inside the label
        ox = (self.width() - self._scaled.width()) // 2
        oy = (self.height() - self._scaled.height()) // 2
        sel = self._rect.translated(-ox, -oy).intersected(
            QRect(0, 0, self._scaled.width(), self._scaled.height())
        )
        if sel.isEmpty():
            return None
        sx = self._source.width() / self._scaled.width()
        sy = self._source.height() / self._scaled.height()
        return QRect(
            int(sel.x() * sx),
            int(sel.y() * sy),
            int(sel.width() * sx),
            int(sel.height() * sy),
        )


class CropDialog(QDialog):
    """Drag-to-select crop dialog. Returns ``(x, y, w, h)`` in source pixels."""

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crop")
        self.resize(900, 700)
        v = QVBoxLayout(self)
        self._canvas = _CropCanvas(pixmap, self)
        v.addWidget(self._canvas, 1)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def result_rect(self) -> tuple[int, int, int, int] | None:
        r = self._canvas.source_rect()
        if r is None:
            return None
        return r.x(), r.y(), r.width(), r.height()
