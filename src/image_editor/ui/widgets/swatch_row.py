from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

# (label, temperature, tint, saturation, vibrance)
PRESETS: list[tuple[str, int, int, int, int]] = [
    ("Neutral", 0, 0, 0, 0),
    ("Warm", 30, 5, 0, 10),
    ("Cool", -30, -5, 0, 10),
    ("Punchy", 0, 0, 20, 25),
    ("Faded", 0, 0, -25, 0),
    ("B&W", 0, 0, -100, 0),
    ("Cinema", -10, -15, -5, 20),
    ("Sunset", 45, 10, 10, 15),
]

# Visual swatch color per preset (for the row pill)
COLORS = {
    "Neutral": "#8B95A3",
    "Warm": "#FFB87A",
    "Cool": "#7BB6FF",
    "Punchy": "#FF6E91",
    "Faded": "#C2B7A8",
    "B&W": "#E6E8EB",
    "Cinema": "#7A86FF",
    "Sunset": "#FF8A5C",
}


class SwatchRow(QFrame):
    """Horizontal row of color preset pills."""

    presetChosen = Signal(str, int, int, int, int)  # name, temp, tint, sat, vibr

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelDeep")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 8, 12, 10)
        outer.setSpacing(4)

        title = QLabel("LOOKS")
        title.setObjectName("H2")
        outer.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(8)
        row.setContentsMargins(0, 0, 0, 0)
        self._buttons: list[QPushButton] = []
        for name, t, ti, s, v in PRESETS:
            btn = QPushButton()
            btn.setObjectName("Swatch")
            btn.setCheckable(True)
            btn.setToolTip(name)
            color = COLORS.get(name, "#5AB0FF")
            btn.setStyleSheet(f"QPushButton#Swatch{{background-color:{color};}}")
            btn.clicked.connect(
                lambda _checked, nm=name, tt=t, tn=ti, ss=s, vv=v: self._emit(nm, tt, tn, ss, vv)
            )
            self._buttons.append(btn)
            row.addWidget(btn)
        row.addStretch(1)
        outer.addLayout(row)

    def _emit(self, name: str, t: int, ti: int, s: int, v: int) -> None:
        # Only one swatch checked at a time
        sender = self.sender()
        for b in self._buttons:
            if b is not sender:
                b.setChecked(False)
        self.presetChosen.emit(name, t, ti, s, v)
