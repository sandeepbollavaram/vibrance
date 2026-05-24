from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from image_editor.config import APP_NAME, APP_TAGLINE
from image_editor.ui.widgets.section_card import SectionCard
from image_editor.ui.widgets.slider_row import SliderRow


# --------- request payloads ------------------------------------------


@dataclass
class CompressRequest:
    """Settings for compressing the current preview image."""
    fmt: str                 # jpg | png | webp
    quality: int             # 1..100
    target_kb: float         # 0 = no target
    resize_width: int        # 0 = keep
    resize_height: int       # 0 = keep
    keep_aspect: bool
    strip_metadata: bool


@dataclass
class BatchCompressRequest:
    in_dir: str
    out_dir: str
    fmt: str
    quality: int
    target_kb: float
    long_edge: int           # 0 = keep
    strip_metadata: bool


# --------- panel ----------------------------------------------------


class CompressorPanel(QFrame):
    """Right-pane view shown when the Compressor tool is selected. Two cards:

        1. Compress Current Image  — operates on the loaded preview
        2. Batch Compress Images   — operates on a whole folder

    All work is delegated to the MainWindow; this widget only collects input
    and surfaces progress/result strings.
    """

    estimateRequested = Signal(object)        # CompressRequest
    previewRequested = Signal(object)
    saveCurrentRequested = Signal(object)
    batchRequested = Signal(object)           # BatchCompressRequest
    cancelBatchRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")
        self.setMinimumWidth(340)
        self.setMaximumWidth(460)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # --- Brand header ---
        brand = QLabel(APP_NAME)
        brand.setObjectName("Brand")
        sub = QLabel(APP_TAGLINE)
        sub.setObjectName("BrandSub")
        root.addWidget(brand)
        root.addWidget(sub)

        # --- Title row ---
        title = QLabel("Compressor")
        title.setStyleSheet(
            "color:#FFFFFF; font-size:16px; font-weight:600; padding-top:4px;"
        )
        root.addWidget(title)

        # --- Mode toggle ---
        mode_row = QHBoxLayout()
        mode_row.setSpacing(0)
        self.btn_mode_single = QPushButton("Current image")
        self.btn_mode_batch = QPushButton("Batch folder")
        for b in (self.btn_mode_single, self.btn_mode_batch):
            b.setObjectName("Segment")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            mode_row.addWidget(b)
        mode_row.addStretch(1)
        self.btn_mode_single.setChecked(True)
        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)
        self._mode_group.addButton(self.btn_mode_single, 0)
        self._mode_group.addButton(self.btn_mode_batch, 1)
        self.btn_mode_single.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        self.btn_mode_batch.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        root.addLayout(mode_row)

        # --- Stack ---
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_single_view())
        self._stack.addWidget(self._build_batch_view())
        root.addWidget(self._stack, 1)

        # --- Stable action bar at the bottom (changes per mode) ---
        self._actions_single = QFrame()
        self._actions_single.setObjectName("ActionBar")
        bs = QHBoxLayout(self._actions_single)
        bs.setContentsMargins(10, 8, 10, 8)
        bs.setSpacing(8)
        self.btn_estimate = QPushButton("Estimate")
        self.btn_estimate.setObjectName("Ghost")
        self.btn_preview = QPushButton("Preview")
        self.btn_preview.setObjectName("Ghost")
        self.btn_save_compressed = QPushButton("Save Compressed")
        self.btn_save_compressed.setObjectName("Primary")
        bs.addWidget(self.btn_estimate)
        bs.addWidget(self.btn_preview)
        bs.addWidget(self.btn_save_compressed, 1)

        self._actions_batch = QFrame()
        self._actions_batch.setObjectName("ActionBar")
        bb = QHBoxLayout(self._actions_batch)
        bb.setContentsMargins(10, 8, 10, 8)
        bb.setSpacing(8)
        self.btn_batch_cancel = QPushButton("Cancel")
        self.btn_batch_cancel.setObjectName("Ghost")
        self.btn_batch_cancel.setEnabled(False)
        self.btn_batch_run = QPushButton("Start Batch Compress")
        self.btn_batch_run.setObjectName("Primary")
        bb.addWidget(self.btn_batch_cancel)
        bb.addWidget(self.btn_batch_run, 1)

        self._action_stack = QStackedWidget()
        self._action_stack.addWidget(self._actions_single)
        self._action_stack.addWidget(self._actions_batch)
        root.addWidget(self._action_stack)

        # Sync action stack with mode
        self.btn_mode_single.clicked.connect(lambda: self._action_stack.setCurrentIndex(0))
        self.btn_mode_batch.clicked.connect(lambda: self._action_stack.setCurrentIndex(1))

        # Wiring
        self.btn_estimate.clicked.connect(
            lambda: self.estimateRequested.emit(self.current_request())
        )
        self.btn_preview.clicked.connect(
            lambda: self.previewRequested.emit(self.current_request())
        )
        self.btn_save_compressed.clicked.connect(
            lambda: self.saveCurrentRequested.emit(self.current_request())
        )
        self.btn_batch_run.clicked.connect(self._emit_batch)
        self.btn_batch_cancel.clicked.connect(self.cancelBatchRequested)

    # ----- build sections -----

    def _build_single_view(self) -> QWidget:
        host = QWidget()
        outer = QVBoxLayout(host)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        # Hint
        hint = QLabel("Reduce the file size of the currently loaded image.")
        hint.setProperty("role", "caption")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        # Format & quality
        fmt_card = SectionCard("FORMAT & QUALITY")
        fr = QHBoxLayout()
        fr.setSpacing(8)
        self.s_fmt = QComboBox()
        self.s_fmt.addItems(["jpg", "png", "webp"])
        fr.addWidget(QLabel("Format"))
        fr.addWidget(self.s_fmt, 1)
        fmt_card.add_layout(fr)
        self.s_quality = SliderRow("Quality", 1, 100, 80)
        fmt_card.add(self.s_quality)
        outer.addWidget(fmt_card)

        # Target file size
        tgt_card = SectionCard("TARGET FILE SIZE")
        tr = QHBoxLayout()
        tr.setSpacing(8)
        self.s_target = QDoubleSpinBox()
        self.s_target.setRange(0, 999_999)
        self.s_target.setDecimals(0)
        self.s_target.setSpecialValueText("Off")
        self.s_target.setValue(0)
        self.s_unit = QComboBox()
        self.s_unit.addItems(["KB", "MB"])
        tr.addWidget(QLabel("Target"))
        tr.addWidget(self.s_target, 1)
        tr.addWidget(self.s_unit)
        tgt_card.add_layout(tr)
        hint2 = QLabel("Vibrance binary-searches the encoder quality "
                       "until the output is at or just under your target.")
        hint2.setProperty("role", "caption")
        hint2.setWordWrap(True)
        tgt_card.add(hint2)
        outer.addWidget(tgt_card)

        # Resize
        size_card = SectionCard("RESIZE")
        sr = QHBoxLayout()
        sr.setSpacing(8)
        self.s_w = QSpinBox()
        self.s_w.setRange(0, 16384)
        self.s_w.setSpecialValueText("Auto")
        self.s_w.setSuffix(" px")
        self.s_h = QSpinBox()
        self.s_h.setRange(0, 16384)
        self.s_h.setSpecialValueText("Auto")
        self.s_h.setSuffix(" px")
        sr.addWidget(QLabel("Width"))
        sr.addWidget(self.s_w, 1)
        sr.addSpacing(6)
        sr.addWidget(QLabel("Height"))
        sr.addWidget(self.s_h, 1)
        size_card.add_layout(sr)
        self.s_keep = QCheckBox("Keep aspect ratio")
        self.s_keep.setChecked(True)
        size_card.add(self.s_keep)
        outer.addWidget(size_card)

        # Options
        opt_card = SectionCard("OPTIONS")
        self.s_strip = QCheckBox("Strip EXIF / metadata")
        self.s_strip.setChecked(True)
        opt_card.add(self.s_strip)
        outer.addWidget(opt_card)

        # Result
        self.result_label = QLabel("")
        self.result_label.setStyleSheet(
            "color:#5AB0FF; font-weight:600; padding:4px 0;"
        )
        self.result_label.setWordWrap(True)
        outer.addWidget(self.result_label)

        outer.addStretch(1)

        return self._scroll_wrap(host)

    def _build_batch_view(self) -> QWidget:
        host = QWidget()
        outer = QVBoxLayout(host)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        hint = QLabel("Compress every image in a folder. Originals are never "
                      "overwritten — output goes to the folder you choose.")
        hint.setProperty("role", "caption")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        # Folders
        folders_card = SectionCard("FOLDERS")
        in_row = QHBoxLayout()
        in_row.setSpacing(8)
        self.b_in = QLineEdit()
        self.b_in.setPlaceholderText("Input folder…")
        self.b_in.textChanged.connect(self._update_count)
        in_browse = QPushButton("Browse")
        in_browse.clicked.connect(self._pick_in)
        in_row.addWidget(QLabel("Input"))
        in_row.addWidget(self.b_in, 1)
        in_row.addWidget(in_browse)
        folders_card.add_layout(in_row)

        out_row = QHBoxLayout()
        out_row.setSpacing(8)
        self.b_out = QLineEdit()
        self.b_out.setPlaceholderText("Output folder…")
        out_browse = QPushButton("Browse")
        out_browse.clicked.connect(self._pick_out)
        out_row.addWidget(QLabel("Output"))
        out_row.addWidget(self.b_out, 1)
        out_row.addWidget(out_browse)
        folders_card.add_layout(out_row)

        self.count_label = QLabel("")
        self.count_label.setProperty("role", "caption")
        folders_card.add(self.count_label)
        outer.addWidget(folders_card)

        # Format + quality
        fmt_card = SectionCard("FORMAT & QUALITY")
        f_row = QHBoxLayout()
        f_row.setSpacing(8)
        self.b_fmt = QComboBox()
        self.b_fmt.addItems(["jpg", "png", "webp", "(keep original)"])
        f_row.addWidget(QLabel("Format"))
        f_row.addWidget(self.b_fmt, 1)
        fmt_card.add_layout(f_row)
        self.b_quality = SliderRow("Quality", 1, 100, 80)
        fmt_card.add(self.b_quality)

        t_row = QHBoxLayout()
        t_row.setSpacing(8)
        self.b_target = QDoubleSpinBox()
        self.b_target.setRange(0, 999_999)
        self.b_target.setDecimals(0)
        self.b_target.setSpecialValueText("Off")
        self.b_unit = QComboBox()
        self.b_unit.addItems(["KB", "MB"])
        t_row.addWidget(QLabel("Target"))
        t_row.addWidget(self.b_target, 1)
        t_row.addWidget(self.b_unit)
        fmt_card.add_layout(t_row)
        outer.addWidget(fmt_card)

        # Resize
        sz_card = SectionCard("RESIZE")
        long_row = QHBoxLayout()
        long_row.setSpacing(8)
        self.b_long = QSpinBox()
        self.b_long.setRange(0, 16384)
        self.b_long.setSpecialValueText("Keep")
        self.b_long.setSuffix(" px")
        long_row.addWidget(QLabel("Long edge"))
        long_row.addWidget(self.b_long, 1)
        sz_card.add_layout(long_row)
        outer.addWidget(sz_card)

        # Options
        opt_card = SectionCard("OPTIONS")
        self.b_strip = QCheckBox("Strip EXIF / metadata")
        self.b_strip.setChecked(True)
        opt_card.add(self.b_strip)
        outer.addWidget(opt_card)

        # Progress + summary
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        outer.addWidget(self.progress)

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("color:#5AB0FF; font-weight:600; padding:4px 0;")
        self.summary_label.setWordWrap(True)
        outer.addWidget(self.summary_label)

        outer.addStretch(1)
        return self._scroll_wrap(host)

    @staticmethod
    def _scroll_wrap(host: QWidget) -> QScrollArea:
        s = QScrollArea()
        s.setFrameShape(QFrame.NoFrame)
        s.setWidgetResizable(True)
        s.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        s.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        s.setWidget(host)
        return s

    # ----- folder pickers / scan -----

    def _pick_in(self) -> None:
        p = QFileDialog.getExistingDirectory(self, "Select input folder")
        if p:
            self.b_in.setText(p)

    def _pick_out(self) -> None:
        p = QFileDialog.getExistingDirectory(self, "Select output folder")
        if p:
            self.b_out.setText(p)

    def _update_count(self) -> None:
        from image_editor.config import SUPPORTED_EXTS
        folder = Path(self.b_in.text().strip())
        if not folder.is_dir():
            self.count_label.setText("")
            return
        files = [p for p in folder.iterdir()
                 if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS]
        self.count_label.setText(
            f"{len(files)} image(s) found" if files else "No images found in folder"
        )

    # ----- request builders -----

    def current_request(self) -> CompressRequest:
        target_kb = float(self.s_target.value())
        if self.s_unit.currentText() == "MB":
            target_kb *= 1024
        return CompressRequest(
            fmt=self.s_fmt.currentText(),
            quality=self.s_quality.value(),
            target_kb=target_kb,
            resize_width=self.s_w.value(),
            resize_height=self.s_h.value(),
            keep_aspect=self.s_keep.isChecked(),
            strip_metadata=self.s_strip.isChecked(),
        )

    def _emit_batch(self) -> None:
        target_kb = float(self.b_target.value())
        if self.b_unit.currentText() == "MB":
            target_kb *= 1024
        req = BatchCompressRequest(
            in_dir=self.b_in.text().strip(),
            out_dir=self.b_out.text().strip(),
            fmt=self.b_fmt.currentText(),
            quality=self.b_quality.value(),
            target_kb=target_kb,
            long_edge=self.b_long.value(),
            strip_metadata=self.b_strip.isChecked(),
        )
        self.btn_batch_run.setEnabled(False)
        self.btn_batch_cancel.setEnabled(True)
        self.summary_label.setText("Running…")
        self.progress.setValue(0)
        self.batchRequested.emit(req)

    # ----- public hooks (called by MainWindow) -----

    def set_single_result(self, text: str) -> None:
        self.result_label.setText(text)

    def set_batch_progress(self, pct: int) -> None:
        self.progress.setValue(pct)

    def set_batch_summary(self, text: str) -> None:
        self.summary_label.setText(text)
        self.btn_batch_run.setEnabled(True)
        self.btn_batch_cancel.setEnabled(False)
