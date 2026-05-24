from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QToolButton,
)

from image_editor.ui.icons import icon


class ZoomBar(QFrame):
    """Floating bottom toolbar: minus / slider / plus / readout / fit.

    Slider range is mapped 0..100 to a log-scale zoom 0.1× .. 10× so the
    middle of the slider is 1.0× (no zoom).
    """

    zoomChanged = Signal(float)
    fitRequested = Signal()
    compareRequested = Signal()

    MIN = 0.1
    MAX = 10.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ZoomBar")
        self.setFixedHeight(48)

        h = QHBoxLayout(self)
        h.setContentsMargins(12, 6, 12, 6)
        h.setSpacing(10)

        self.btn_minus = QToolButton()
        self.btn_minus.setIcon(icon("zoom_out"))
        self.btn_minus.setIconSize(QSize(18, 18))
        self.btn_minus.setFixedSize(32, 32)
        self.btn_minus.setToolTip("Zoom out")
        self.btn_minus.setCursor(Qt.PointingHandCursor)
        self.btn_minus.setAutoRaise(True)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        self.slider.setFixedWidth(220)

        self.btn_plus = QToolButton()
        self.btn_plus.setIcon(icon("zoom_in"))
        self.btn_plus.setIconSize(QSize(18, 18))
        self.btn_plus.setFixedSize(32, 32)
        self.btn_plus.setToolTip("Zoom in")
        self.btn_plus.setCursor(Qt.PointingHandCursor)
        self.btn_plus.setAutoRaise(True)

        self.lbl = QLabel("100%")
        self.lbl.setProperty("role", "value")
        self.lbl.setFixedWidth(54)
        self.lbl.setAlignment(Qt.AlignCenter)

        self.btn_fit = QPushButton("Fit")
        self.btn_fit.setObjectName("Ghost")
        self.btn_fit.setIcon(icon("fit"))
        self.btn_fit.setIconSize(QSize(16, 16))
        self.btn_fit.setToolTip("Fit to window (Ctrl+0)")

        self.btn_compare = QPushButton("Compare")
        self.btn_compare.setObjectName("Ghost")
        self.btn_compare.setIcon(icon("compare"))
        self.btn_compare.setIconSize(QSize(16, 16))
        self.btn_compare.setToolTip("Before / after (Ctrl+/)")

        h.addWidget(self.btn_minus)
        h.addWidget(self.slider)
        h.addWidget(self.btn_plus)
        h.addWidget(self.lbl)
        h.addStretch(1)
        h.addWidget(self.btn_compare)
        h.addWidget(self.btn_fit)

        self.btn_minus.clicked.connect(lambda: self._nudge(-5))
        self.btn_plus.clicked.connect(lambda: self._nudge(+5))
        self.btn_fit.clicked.connect(self.fitRequested)
        self.btn_compare.clicked.connect(self.compareRequested)
        self.slider.valueChanged.connect(self._on_changed)

    def _slider_to_zoom(self, v: int) -> float:
        # 0..100 -> log scale, 50 == 1.0×
        import math
        t = (v - 50) / 50.0          # -1..1
        return self.MIN if v == 0 else self.MAX if v == 100 else 10 ** (t * 1.0)

    def _zoom_to_slider(self, z: float) -> int:
        import math
        z = max(self.MIN, min(self.MAX, z))
        return int(50 + math.log10(z) * 50)

    def _on_changed(self, v: int) -> None:
        z = self._slider_to_zoom(v)
        self.lbl.setText(f"{int(z * 100)}%")
        self.zoomChanged.emit(z)

    def _nudge(self, delta: int) -> None:
        self.slider.setValue(max(0, min(100, self.slider.value() + delta)))

    def set_zoom(self, zoom: float) -> None:
        self.slider.blockSignals(True)
        self.slider.setValue(self._zoom_to_slider(zoom))
        self.slider.blockSignals(False)
        self.lbl.setText(f"{int(zoom * 100)}%")
