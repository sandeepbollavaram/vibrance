from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class OutputPanel(QFrame):
    """Right column: log, output list, compare button, progress."""

    compareRequested = Signal()
    outputClicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(8)

        title = QLabel("ACTIVITY")
        title.setObjectName("H2")
        root.addWidget(title)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(140)
        root.addWidget(self.log_box)

        out_title = QLabel("OUTPUT FILES")
        out_title.setObjectName("H2")
        root.addWidget(out_title)

        self.output_list = QListWidget()
        root.addWidget(self.output_list, 1)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.hide()
        root.addWidget(self.progress)

        row = QHBoxLayout()
        self.compare_btn = QPushButton("Compare Before / After")
        row.addStretch(1)
        row.addWidget(self.compare_btn)
        root.addLayout(row)

        self.compare_btn.clicked.connect(self.compareRequested)
        self.output_list.itemClicked.connect(
            lambda item: self.outputClicked.emit(item.data(0x0100) or item.text())
        )

    def append_log(self, line: str) -> None:
        self.log_box.append(line)

    def set_log_text(self, text: str) -> None:
        self.log_box.setPlainText(text)

    def add_output(self, path: str) -> None:
        from pathlib import Path
        from PySide6.QtWidgets import QListWidgetItem
        item = QListWidgetItem(Path(path).name)
        item.setData(0x0100, path)
        self.output_list.addItem(item)

    def show_progress(self, show: bool) -> None:
        self.progress.setVisible(show)
        if show:
            self.progress.setValue(0)

    def set_progress(self, pct: int) -> None:
        self.progress.setValue(pct)
