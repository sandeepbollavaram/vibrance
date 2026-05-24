from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)


@dataclass
class ExportRequest:
    out_path: str
    fmt: str  # jpg | png | webp
    mode: str  # "quality" | "target_size"
    quality: int  # 1..100 (quality mode)
    target_kb: float  # KB ceiling (target_size mode)
    max_long_edge: int  # 0 = no resize
    strip_metadata: bool


class ExportDialog(QDialog):
    """Export-with-compression dialog.

    Two modes:
      • Quality        — pick a quality 1..100.
      • Target size    — pick a KB ceiling; encoder binary-searches quality.

    Optional: cap the long edge (resize for web), strip metadata.
    """

    def __init__(self, suggested_name: str = "export.jpg", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export / Compress")
        self.setMinimumWidth(460)

        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(10)

        # Output path
        path_row = QHBoxLayout()
        self.path_edit = QLineEdit(suggested_name)
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._pick_path)
        path_row.addWidget(QLabel("Save to:"))
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse)
        v.addLayout(path_row)

        # Format
        fmt_row = QHBoxLayout()
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["jpg", "png", "webp"])
        self.fmt_combo.currentTextChanged.connect(self._on_fmt_change)
        fmt_row.addWidget(QLabel("Format:"))
        fmt_row.addWidget(self.fmt_combo)
        fmt_row.addStretch(1)
        v.addLayout(fmt_row)

        # Mode
        self.mode_group = QButtonGroup(self)
        self.mode_quality = QRadioButton("Quality (1–100)")
        self.mode_size = QRadioButton("Target file size (KB)")
        self.mode_quality.setChecked(True)
        self.mode_group.addButton(self.mode_quality, 0)
        self.mode_group.addButton(self.mode_size, 1)
        v.addWidget(self.mode_quality)
        v.addWidget(self.mode_size)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(85)

        self.target_spin = QDoubleSpinBox()
        self.target_spin.setRange(5, 100_000)
        self.target_spin.setSuffix(" KB")
        self.target_spin.setDecimals(0)
        self.target_spin.setValue(500)

        self.long_edge_spin = QSpinBox()
        self.long_edge_spin.setRange(0, 16384)
        self.long_edge_spin.setSuffix(" px")
        self.long_edge_spin.setSpecialValueText("Original")
        self.long_edge_spin.setValue(0)

        self.strip_check = QCheckBox("Strip EXIF / metadata")
        self.strip_check.setChecked(True)

        form.addRow("Quality:", self.quality_spin)
        form.addRow("Target size:", self.target_spin)
        form.addRow("Max long edge:", self.long_edge_spin)
        form.addRow("", self.strip_check)
        v.addLayout(form)

        self.mode_group.idToggled.connect(self._sync_mode_enabled)
        self._sync_mode_enabled()

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("Export")
        bb.button(QDialogButtonBox.Ok).setObjectName("Primary")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    # ----- internals -----
    def _on_fmt_change(self, fmt: str) -> None:
        path = self.path_edit.text().strip() or "export"
        stem = Path(path).stem or "export"
        parent = str(Path(path).parent) if Path(path).parent != Path() else ""
        self.path_edit.setText(str(Path(parent) / f"{stem}.{fmt}") if parent else f"{stem}.{fmt}")
        # PNG can't hit a size target meaningfully — disable target mode for png.
        png = fmt == "png"
        self.mode_size.setEnabled(not png)
        if png and self.mode_size.isChecked():
            self.mode_quality.setChecked(True)

    def _sync_mode_enabled(self, *_) -> None:
        use_q = self.mode_quality.isChecked()
        self.quality_spin.setEnabled(use_q)
        self.target_spin.setEnabled(not use_q)

    def _pick_path(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save As",
            self.path_edit.text(),
            "JPEG (*.jpg);;PNG (*.png);;WebP (*.webp)",
        )
        if path:
            self.path_edit.setText(path)
            ext = Path(path).suffix.lstrip(".").lower()
            if ext in ("jpg", "jpeg", "png", "webp"):
                self.fmt_combo.setCurrentText("jpg" if ext == "jpeg" else ext)

    # ----- API -----
    def request(self) -> ExportRequest:
        return ExportRequest(
            out_path=self.path_edit.text().strip(),
            fmt=self.fmt_combo.currentText(),
            mode="quality" if self.mode_quality.isChecked() else "target_size",
            quality=self.quality_spin.value(),
            target_kb=self.target_spin.value(),
            max_long_edge=self.long_edge_spin.value(),
            strip_metadata=self.strip_check.isChecked(),
        )
