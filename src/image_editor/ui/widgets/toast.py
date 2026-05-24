from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    Qt,
    QTimer,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QWidget,
)


class Toast(QFrame):
    """Floating notification anchored to the bottom-center of its parent.
    Auto-fades after ``duration_ms``."""

    def __init__(self, parent: QWidget, message: str, kind: str = "info",
                 duration_ms: int = 2500):
        super().__init__(parent)
        self.setObjectName("ToastError" if kind == "error" else "Toast")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._duration = duration_ms

        h = QHBoxLayout(self)
        h.setContentsMargins(14, 10, 16, 10)
        h.setSpacing(10)

        glyph = QLabel("!" if kind == "error" else "✓")
        glyph.setStyleSheet(
            "color:#FF8FA6; font-weight:800; font-size:14px;" if kind == "error"
            else "color:#5AB0FF; font-weight:800; font-size:14px;"
        )
        h.addWidget(glyph)

        lbl = QLabel(message)
        lbl.setStyleSheet("color:#FFFFFF; font-size:13px;")
        lbl.setWordWrap(True)
        h.addWidget(lbl, 1)

        self.adjustSize()

        # Opacity effect for fade in/out
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)

        self._anim_in = QPropertyAnimation(self._opacity, b"opacity", self)
        self._anim_in.setDuration(160)
        self._anim_in.setStartValue(0.0)
        self._anim_in.setEndValue(1.0)
        self._anim_in.setEasingCurve(QEasingCurve.OutCubic)

        self._anim_out = QPropertyAnimation(self._opacity, b"opacity", self)
        self._anim_out.setDuration(220)
        self._anim_out.setStartValue(1.0)
        self._anim_out.setEndValue(0.0)
        self._anim_out.setEasingCurve(QEasingCurve.InCubic)
        self._anim_out.finished.connect(self.close)

    def show_at_bottom(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            self.show()
            return
        self.adjustSize()
        x = (parent.width() - self.width()) // 2
        y = parent.height() - self.height() - 32
        self.move(QPoint(max(8, x), max(8, y)))
        self.show()
        self.raise_()
        self._anim_in.start()
        QTimer.singleShot(self._duration, self._anim_out.start)


def show_toast(parent: QWidget, message: str, kind: str = "info",
               duration_ms: int = 2500) -> Toast:
    t = Toast(parent, message, kind=kind, duration_ms=duration_ms)
    t.show_at_bottom()
    return t
