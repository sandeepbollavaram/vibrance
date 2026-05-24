from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPixmap, QWheelEvent
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView


class ZoomableImageView(QGraphicsView):
    """QGraphicsView that supports wheel-zoom and double-click fit."""

    MIN_SCALE = 0.05
    MAX_SCALE = 40.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)

        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setBackgroundBrush(Qt.black)
        self._scale = 1.0

    def set_image(self, pixmap: QPixmap) -> None:
        self._pixmap_item.setPixmap(pixmap)
        self.setSceneRect(QRectF(pixmap.rect()))
        self.reset_view()

    def reset_view(self) -> None:
        self.resetTransform()
        self._scale = 1.0
        if not self._pixmap_item.pixmap().isNull():
            self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        new_scale = self._scale * factor
        if not (self.MIN_SCALE <= new_scale <= self.MAX_SCALE):
            return
        self._scale = new_scale
        self.scale(factor, factor)

    def mouseDoubleClickEvent(self, event):  # noqa: N802
        self.reset_view()
