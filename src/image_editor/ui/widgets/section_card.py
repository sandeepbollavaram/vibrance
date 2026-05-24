from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class SectionCard(QFrame):
    """A titled section container. Reusable across tabs to enforce consistent
    spacing and prevent overlap between groups of sliders / controls."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("Section")
        self._v = QVBoxLayout(self)
        self._v.setContentsMargins(14, 12, 14, 14)
        self._v.setSpacing(4)

        if title:
            lbl = QLabel(title)
            lbl.setObjectName("H2")
            self._v.addWidget(lbl)

    def add(self, widget: QWidget) -> None:
        self._v.addWidget(widget)

    def add_layout(self, layout) -> None:
        self._v.addLayout(layout)

    def add_spacing(self, px: int = 4) -> None:
        self._v.addSpacing(px)
