from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from image_editor.config import SUPPORTED_EXTS


class BatchDialog(QDialog):
    """Modal for running edits across a folder. The dialog only collects
    settings and reports progress; the actual processing is delegated to the
    parent via ``runRequested(settings_dict)``."""

    runRequested = Signal(dict)
    cancelRequested = Signal()

    def __init__(self, current_params, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Processing")
        self.setMinimumWidth(560)
        self._params = current_params

        v = QVBoxLayout(self)
        v.setContentsMargins(18, 18, 18, 18)
        v.setSpacing(12)

        title = QLabel("Apply current edits to a folder of images")
        title.setStyleSheet("font-size:15px; font-weight:600; color:#FFFFFF;")
        v.addWidget(title)

        # Input folder
        in_row = QHBoxLayout()
        in_row.setSpacing(8)
        self.in_edit = QLineEdit()
        self.in_edit.setPlaceholderText("Input folder…")
        self.btn_in = QPushButton("Browse")
        self.btn_in.clicked.connect(self._pick_in)
        in_row.addWidget(QLabel("Input"))
        in_row.addWidget(self.in_edit, 1)
        in_row.addWidget(self.btn_in)
        v.addLayout(in_row)

        # Output folder
        out_row = QHBoxLayout()
        out_row.setSpacing(8)
        self.out_edit = QLineEdit()
        self.out_edit.setPlaceholderText("Output folder (defaults to <input>/edited)")
        self.btn_out = QPushButton("Browse")
        self.btn_out.clicked.connect(self._pick_out)
        out_row.addWidget(QLabel("Output"))
        out_row.addWidget(self.out_edit, 1)
        out_row.addWidget(self.btn_out)
        v.addLayout(out_row)

        # Options
        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        self.fmt = QComboBox()
        self.fmt.addItems(["jpg", "png", "webp", "(keep original)"])
        form.addRow("Output format", self.fmt)

        self.quality = QSpinBox()
        self.quality.setRange(1, 100)
        self.quality.setValue(90)
        form.addRow("Quality", self.quality)

        self.long_edge = QSpinBox()
        self.long_edge.setRange(0, 16384)
        self.long_edge.setSpecialValueText("Original")
        self.long_edge.setSuffix(" px")
        form.addRow("Resize long edge", self.long_edge)

        self.strip = QCheckBox("Strip EXIF / metadata")
        self.strip.setChecked(True)
        form.addRow("", self.strip)

        v.addLayout(form)

        self.count_label = QLabel("")
        self.count_label.setProperty("role", "caption")
        v.addWidget(self.count_label)

        # Progress + actions
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.hide()
        v.addWidget(self.progress)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("Ghost")
        self.btn_cancel.clicked.connect(self._cancel)
        self.btn_run = QPushButton("Run batch")
        self.btn_run.setObjectName("Primary")
        self.btn_run.clicked.connect(self._run)
        actions.addWidget(self.btn_cancel)
        actions.addWidget(self.btn_run)
        v.addLayout(actions)

        self.in_edit.textChanged.connect(self._update_count)

    # --- file pickers ---
    def _pick_in(self) -> None:
        p = QFileDialog.getExistingDirectory(self, "Select input folder")
        if p:
            self.in_edit.setText(p)

    def _pick_out(self) -> None:
        p = QFileDialog.getExistingDirectory(self, "Select output folder")
        if p:
            self.out_edit.setText(p)

    # --- helpers ---
    def _scan(self) -> list[Path]:
        folder = Path(self.in_edit.text().strip())
        if not folder.is_dir():
            return []
        return sorted(
            p for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
        )

    def _update_count(self) -> None:
        files = self._scan()
        self.count_label.setText(
            f"{len(files)} image(s) found." if files else "No images found in folder."
        )

    # --- actions ---
    def _run(self) -> None:
        files = self._scan()
        if not files:
            self.count_label.setText("Pick a folder containing images first.")
            return
        self.progress.show()
        self.btn_run.setEnabled(False)
        self.runRequested.emit({
            "files": [str(p) for p in files],
            "out_dir": self.out_edit.text().strip(),
            "fmt": self.fmt.currentText(),
            "quality": self.quality.value(),
            "long_edge": self.long_edge.value(),
            "strip_metadata": self.strip.isChecked(),
            "params": self._params,
        })

    def _cancel(self) -> None:
        self.cancelRequested.emit()
        self.reject()

    # --- external progress hook ---
    def set_progress(self, pct: int) -> None:
        self.progress.setValue(pct)

    def finished(self, ok: int, fail: int) -> None:
        self.btn_run.setEnabled(True)
        self.count_label.setText(f"Completed: {ok} succeeded, {fail} failed.")
