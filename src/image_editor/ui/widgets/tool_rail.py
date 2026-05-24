from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QToolButton,
    QVBoxLayout,
)

from image_editor.ui.icons import icon


class ToolRail(QFrame):
    """Slim vertical rail with local-SVG icons + a short text label below.
    Uses ``QToolButton`` with ``ToolButtonTextUnderIcon`` for clean icon-above-
    text layout that's impossible to break with stylesheet quirks."""

    toolChanged = Signal(str)

    TOOLS = [
        ("open", "Open", "Open image (Ctrl+O)"),
        ("crop", "Crop", "Crop"),
        ("adjust", "Adjust", "Adjustments"),
        ("filters", "Filters", "Color & filter presets"),
        ("batch", "Batch", "Batch processing (Ctrl+B)"),
        ("compressor", "Compress", "File compressor"),
        ("compare", "Compare", "Before / after (Ctrl+/)"),
        ("export", "Export", "Export / save (Ctrl+E)"),
        ("help", "Help", "Keyboard shortcuts & About"),
    ]

    ICON_SIZE = QSize(20, 20)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Toolrail")
        self.setFixedWidth(76)

        v = QVBoxLayout(self)
        v.setContentsMargins(8, 10, 8, 10)
        v.setSpacing(4)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QToolButton] = {}

        for tid, label, tooltip in self.TOOLS:
            btn = QToolButton()
            btn.setObjectName("ToolButton")
            btn.setText(label)
            btn.setIcon(icon(tid))
            btn.setIconSize(self.ICON_SIZE)
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setCheckable(True)
            btn.setAutoExclusive(False)  # we manage via QButtonGroup
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(54)
            btn.setProperty("toolId", tid)
            btn.toggled.connect(self._on_toggled)
            self._group.addButton(btn)
            self._buttons[tid] = btn
            v.addWidget(btn)

        v.addStretch(1)
        self._buttons["adjust"].setChecked(True)

    def _on_toggled(self, checked: bool) -> None:
        if not checked:
            return
        sender = self.sender()
        if sender is None:
            return
        tid = sender.property("toolId")
        if tid:
            self.toolChanged.emit(tid)

    def select(self, tool_id: str) -> None:
        btn = self._buttons.get(tool_id)
        if btn is not None and not btn.isChecked():
            btn.setChecked(True)

    def currentTool(self) -> str:
        for tid, btn in self._buttons.items():
            if btn.isChecked():
                return tid
        return "adjust"
