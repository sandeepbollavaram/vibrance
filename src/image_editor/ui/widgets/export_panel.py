from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from image_editor.ui.widgets.section_card import SectionCard
from image_editor.ui.widgets.slider_row import SliderRow


@dataclass
class ExportSettings:
    fmt: str = "jpg"               # jpg | png | webp
    quality: int = 90              # 1..100
    resize_width: int = 0          # 0 = keep
    resize_height: int = 0         # 0 = keep
    keep_aspect: bool = True
    strip_metadata: bool = True


class ExportPanel(QWidget):
    """Export tab body. Pure settings widget — emits requests; the
    MainWindow performs the actual file dialog + save."""

    saveCurrentRequested = Signal(object)   # ExportSettings
    saveAsRequested = Signal(object)
    batchExportRequested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(10)

        # Format & quality
        fmt_card = SectionCard("FORMAT & QUALITY")
        form = QFormLayout()
        form.setContentsMargins(0, 4, 0, 0)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["jpg", "png", "webp"])
        form.addRow("Format", self.fmt_combo)
        fmt_card.add_layout(form)

        self.q_slider = SliderRow("Quality", 1, 100, 90)
        fmt_card.add(self.q_slider)
        v.addWidget(fmt_card)

        # Resize
        size_card = SectionCard("RESIZE")
        size_row = QHBoxLayout()
        size_row.setSpacing(8)

        self.w_spin = QSpinBox()
        self.w_spin.setRange(0, 16384)
        self.w_spin.setSpecialValueText("Auto")
        self.w_spin.setSuffix(" px")

        self.h_spin = QSpinBox()
        self.h_spin.setRange(0, 16384)
        self.h_spin.setSpecialValueText("Auto")
        self.h_spin.setSuffix(" px")

        size_row.addWidget(QLabel("Width"))
        size_row.addWidget(self.w_spin, 1)
        size_row.addSpacing(4)
        size_row.addWidget(QLabel("Height"))
        size_row.addWidget(self.h_spin, 1)
        size_card.add_layout(size_row)

        self.keep_aspect = QCheckBox("Keep aspect ratio")
        self.keep_aspect.setChecked(True)
        size_card.add(self.keep_aspect)
        v.addWidget(size_card)

        # Metadata + actions
        opt_card = SectionCard("OPTIONS")
        self.strip = QCheckBox("Strip EXIF / metadata")
        self.strip.setChecked(True)
        opt_card.add(self.strip)
        v.addWidget(opt_card)

        action_card = SectionCard("EXPORT")
        save_row = QHBoxLayout()
        save_row.setSpacing(8)
        self.btn_save = QPushButton("Save")
        self.btn_save.setObjectName("Ghost")
        self.btn_save_as = QPushButton("Save As…")
        self.btn_save_as.setObjectName("Ghost")
        self.btn_batch = QPushButton("Batch Export…")
        self.btn_batch.setObjectName("Primary")
        save_row.addWidget(self.btn_save)
        save_row.addWidget(self.btn_save_as)
        action_card.add_layout(save_row)
        action_card.add(self.btn_batch)
        v.addWidget(action_card)

        v.addStretch(1)

        self.btn_save.clicked.connect(lambda: self.saveCurrentRequested.emit(self.settings()))
        self.btn_save_as.clicked.connect(lambda: self.saveAsRequested.emit(self.settings()))
        self.btn_batch.clicked.connect(lambda: self.batchExportRequested.emit(self.settings()))

    def settings(self) -> ExportSettings:
        return ExportSettings(
            fmt=self.fmt_combo.currentText(),
            quality=self.q_slider.value(),
            resize_width=self.w_spin.value(),
            resize_height=self.h_spin.value(),
            keep_aspect=self.keep_aspect.isChecked(),
            strip_metadata=self.strip.isChecked(),
        )
