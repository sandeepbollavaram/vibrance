from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from image_editor.config import EditParams


def _bgr_to_pixmap(bgr) -> QPixmap:
    import cv2
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(img)


class PresetGrid(QFrame):
    """Reusable grid of preset cards. Each preset is ``(label, overrides_dict)``
    where overrides_dict is merged onto the current EditParams when chosen.

    The grid lays cards out in 2 columns to stay compact in the right panel.
    Setting the source image via ``set_source_image`` re-renders thumbnails so
    each card previews the actual look applied to the user's photo.
    """

    presetChosen = Signal(str, dict)

    def __init__(self, title: str, presets: list[tuple[str, dict]], parent=None):
        super().__init__(parent)
        self.setObjectName("Section")
        self._presets = presets

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 14)
        outer.setSpacing(8)

        if title:
            lbl = QLabel(title)
            lbl.setObjectName("H2")
            outer.addWidget(lbl)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: list[QPushButton] = []

        for i, (name, _overrides) in enumerate(presets):
            btn = QPushButton(name)
            btn.setObjectName("PresetCard")
            btn.setCheckable(True)
            btn.setIconSize(QSize(70, 44))
            btn.setMinimumHeight(78)
            btn.setMaximumHeight(96)
            btn.clicked.connect(lambda _c, nm=name: self._on_click(nm))
            self._group.addButton(btn)
            self._buttons.append(btn)
            grid.addWidget(btn, i // 2, i % 2)

        outer.addLayout(grid)

    def _on_click(self, name: str) -> None:
        overrides = next((p for n, p in self._presets if n == name), {})
        self.presetChosen.emit(name, overrides)

    def set_source_image(self, source_bgr) -> None:
        """Re-render every card's thumbnail using ``source_bgr``."""
        if source_bgr is None:
            return
        import cv2
        from image_editor.core.filters import apply_all
        h, w = source_bgr.shape[:2]
        scale = 80 / max(h, w)
        thumb_src = (
            cv2.resize(source_bgr, (int(w * scale), int(h * scale)),
                       interpolation=cv2.INTER_AREA)
            if scale < 1.0 else source_bgr
        )
        for btn, (_name, overrides) in zip(self._buttons, self._presets):
            params = replace(EditParams(), **overrides) if overrides else EditParams()
            try:
                rendered = apply_all(thumb_src, params)
            except Exception:
                rendered = thumb_src
            pix = _bgr_to_pixmap(rendered).scaled(
                70, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            btn.setIcon(QIcon(pix))
