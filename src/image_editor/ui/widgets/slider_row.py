from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from image_editor.ui.icons import icon


class SliderRow(QWidget):
    """A single slider control row.

    Layout:
        ┌────────────────────────────────────────┐
        │ Exposure                     -12  [↺] │   header
        │ ─────●──────────────────────────────── │   slider
        └────────────────────────────────────────┘

    Labels are transparent (no ugly black box).
    The reset button is a real SVG icon button that resets to ``default``.
    """

    valueChanged = Signal(int)

    def __init__(
        self,
        label: str,
        minimum: int = -100,
        maximum: int = 100,
        default: int = 0,
        parent=None,
    ):
        super().__init__(parent)
        self._default = default
        self._emitting = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 6, 0, 6)
        root.setSpacing(4)

        # Header: label · stretch · value · reset
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        self._label = QLabel(label)
        self._label.setStyleSheet("background: transparent; color: #C9D2E0; font-size: 12px;")
        self._label.setAttribute(Qt.WA_TranslucentBackground)

        self._value = QLabel(str(default))
        self._value.setStyleSheet(
            "background: transparent; color: #FFFFFF; font-size: 12px;"
            " font-weight: 600; min-width: 32px;"
        )
        self._value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._value.setAttribute(Qt.WA_TranslucentBackground)

        self._reset = QToolButton()
        self._reset.setObjectName("ResetButton")
        self._reset.setIcon(icon("reset"))
        self._reset.setIconSize(QSize(14, 14))
        self._reset.setFixedSize(22, 22)
        self._reset.setCursor(Qt.PointingHandCursor)
        self._reset.setToolTip("Reset")
        self._reset.setAutoRaise(True)

        header.addWidget(self._label)
        header.addStretch(1)
        header.addWidget(self._value)
        header.addWidget(self._reset)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(minimum, maximum)
        self._slider.setValue(default)
        self._slider.setSingleStep(1)
        self._slider.setPageStep(10)

        root.addLayout(header)
        root.addWidget(self._slider)

        self._slider.valueChanged.connect(self._on_slider)
        self._reset.clicked.connect(self.reset)

    # ---- API ----
    def value(self) -> int:
        return self._slider.value()

    def set_value(self, v: int) -> None:
        self._slider.setValue(int(v))

    def reset(self) -> None:
        self.set_value(self._default)

    # ---- internals ----
    def _on_slider(self, v: int) -> None:
        self._value.setText(str(v))
        self._update_reset_visibility(v)
        if self._emitting:
            return
        self.valueChanged.emit(v)

    def _update_reset_visibility(self, v: int) -> None:
        # Subtly fade the reset button when at default
        if v == self._default:
            self._reset.setStyleSheet("QToolButton#ResetButton { opacity: 0.0; }")
            self._reset.setEnabled(False)
        else:
            self._reset.setStyleSheet("")
            self._reset.setEnabled(True)
