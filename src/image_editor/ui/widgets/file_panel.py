from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)

from image_editor.config import SUPPORTED_EXTS


class FilePanel(QFrame):
    """Folder browser + filtered file list. Emits selected file paths."""

    folderChanged = Signal(str)
    fileSelected = Signal(str)
    selectionChanged = Signal(list)  # list[str] absolute paths

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")
        self.setAcceptDrops(True)
        self._folder = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(8)

        title = QLabel("FILES")
        title.setObjectName("H2")
        root.addWidget(title)

        path_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Folder path or drop a folder here…")
        self.browse_btn = QPushButton("Browse")
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(self.browse_btn)
        root.addLayout(path_row)

        filt_row = QHBoxLayout()
        filt_row.addWidget(QLabel("Filter:"))
        self.ext_combo = QComboBox()
        self.ext_combo.addItem("All images")
        for e in SUPPORTED_EXTS:
            self.ext_combo.addItem(e.lstrip("."))
        self.load_btn = QPushButton("Load")
        filt_row.addWidget(self.ext_combo, 1)
        filt_row.addWidget(self.load_btn)
        root.addLayout(filt_row)

        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        root.addWidget(self.list, 1)

        self.count_label = QLabel("")
        self.count_label.setProperty("role", "caption")
        root.addWidget(self.count_label)

        self.browse_btn.clicked.connect(self._browse)
        self.load_btn.clicked.connect(self.reload)
        self.list.itemClicked.connect(self._on_clicked)
        self.list.itemSelectionChanged.connect(self._emit_selection)

    # ----- API -----
    def folder(self) -> str:
        return self._folder

    def selected_paths(self) -> list[str]:
        return [self._abs(i.text()) for i in self.list.selectedItems()]

    # ----- actions -----
    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select folder")
        if folder:
            self.path_edit.setText(folder)
            self.reload()

    def reload(self) -> None:
        folder = self.path_edit.text().strip()
        if not folder or not Path(folder).is_dir():
            self.count_label.setText("Invalid folder")
            return
        self._folder = folder
        self.folderChanged.emit(folder)
        self.list.clear()
        ext_text = self.ext_combo.currentText().lower()
        allowed = SUPPORTED_EXTS if ext_text == "all images" else (f".{ext_text}",)
        files = sorted(
            p.name for p in Path(folder).iterdir() if p.suffix.lower() in allowed
        )
        for f in files:
            self.list.addItem(f)
        self.count_label.setText(f"{len(files)} file(s)")

    def _on_clicked(self, item) -> None:
        self.fileSelected.emit(self._abs(item.text()))

    def _emit_selection(self) -> None:
        self.selectionChanged.emit(self.selected_paths())

    def _abs(self, name: str) -> str:
        return str(Path(self._folder) / name)

    # ----- drag & drop -----
    def dragEnterEvent(self, e):  # noqa: N802
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):  # noqa: N802
        for url in e.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.is_dir():
                self.path_edit.setText(str(p))
                self.reload()
                return
            if p.is_file() and p.parent.is_dir():
                self.path_edit.setText(str(p.parent))
                self.reload()
                return
