from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)


def _bgr_to_pix(bgr) -> QPixmap:
    import cv2
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(img)


class HistoryStrip(QFrame):
    """Horizontal thumbnail strip showing edit snapshots (newest at left)."""

    snapshotChosen = Signal(int)    # index in user-facing order (0 = newest)

    THUMB = QSize(96, 64)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelDeep")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 8, 12, 10)
        outer.setSpacing(4)

        title = QLabel("HISTORY")
        title.setObjectName("H2")
        outer.addWidget(title)

        self._list = QListWidget()
        self._list.setFlow(QListWidget.LeftToRight)
        self._list.setIconSize(self.THUMB)
        self._list.setSpacing(6)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._list.setFixedHeight(self.THUMB.height() + 28)
        self._list.setMovement(QListWidget.Static)
        self._list.setSelectionMode(QListWidget.SingleSelection)
        outer.addWidget(self._list)

        self._list.itemClicked.connect(
            lambda item: self.snapshotChosen.emit(self._list.row(item))
        )

    def clear(self) -> None:
        self._list.clear()

    def add(self, bgr, label: str = "") -> None:
        item = QListWidgetItem()
        item.setIcon(_bgr_to_pix(bgr).scaled(
            self.THUMB, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        if label:
            item.setText(label)
        item.setSizeHint(QSize(self.THUMB.width() + 8, self.THUMB.height() + 24))
        self._list.insertItem(0, item)
        # Cap at 12 entries
        while self._list.count() > 12:
            self._list.takeItem(self._list.count() - 1)
