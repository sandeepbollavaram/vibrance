from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from image_editor.config import APP_NAME, APP_TAGLINE, EditParams
from image_editor.ui.icons import icon
from image_editor.ui.widgets.export_panel import ExportPanel
from image_editor.ui.widgets.preset_grid import PresetGrid
from image_editor.ui.widgets.section_card import SectionCard
from image_editor.ui.widgets.slider_row import SliderRow

# Color presets — applied as EditParams overrides
COLOR_PRESETS: list[tuple[str, dict]] = [
    ("Original", {}),
    ("Vivid", {"saturation": 24, "vibrance": 18, "contrast": 12}),
    ("Warm", {"temperature": 30, "tint": 6, "saturation": 8}),
    ("Cool", {"temperature": -30, "tint": -5, "saturation": 6}),
    ("Mono", {"saturation": -100, "contrast": 14}),
    ("Film", {"contrast": 18, "highlights": -12, "shadows": 12, "fade": 22, "grain": 12}),
    ("Cyber", {"temperature": -22, "tint": 12, "saturation": 24, "blue": 14}),
    ("Soft", {"contrast": -10, "saturation": -8, "fade": 18}),
    ("Matte", {"fade": 38, "contrast": -6, "saturation": -10}),
    ("High Contrast", {"contrast": 32, "clarity": 18}),
]

# Effect presets
EFFECT_PRESETS: list[tuple[str, dict]] = [
    ("Cinematic", {"contrast": 18, "fade": 18, "vignette": 28, "temperature": -8, "tint": -8}),
    ("Portrait Pop", {"clarity": 14, "vibrance": 18, "sharpness": 18, "glow": 12}),
    ("Landscape Boost", {"clarity": 22, "saturation": 14, "vibrance": 16, "sharpness": 22}),
    ("Street", {"contrast": 22, "clarity": 14, "saturation": -10, "grain": 18, "vignette": 18}),
    ("Night", {"shadows": 22, "blacks": 14, "blue": 10, "dehaze": 22, "glow": 14}),
    ("Vintage", {"saturation": -18, "tint": 8, "fade": 28, "grain": 18, "vignette": 22}),
    ("B&&W", {"saturation": -100, "contrast": 18, "clarity": 12, "grain": 14}),
    ("Soft Light", {"highlights": -10, "glow": 18, "fade": 12, "contrast": -6}),
]


# ---------- Tabs ----------------------------------------------------


class _AdjustTab(QWidget):
    paramsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(10)

        basic = SectionCard("BASIC")
        self.exposure = SliderRow("Exposure", -100, 100, 0)
        self.brightness = SliderRow("Brightness", -100, 100, 0)
        self.contrast = SliderRow("Contrast", -100, 100, 0)
        self.highlights = SliderRow("Highlights", -100, 100, 0)
        self.shadows = SliderRow("Shadows", -100, 100, 0)
        self.whites = SliderRow("Whites", -100, 100, 0)
        self.blacks = SliderRow("Blacks", -100, 100, 0)
        for s in (
            self.exposure,
            self.brightness,
            self.contrast,
            self.highlights,
            self.shadows,
            self.whites,
            self.blacks,
        ):
            s.valueChanged.connect(lambda _: self.paramsChanged.emit())
            basic.add(s)
        v.addWidget(basic)

        detail = SectionCard("DETAIL")
        self.sharpness = SliderRow("Sharpness", 0, 100, 0)
        self.clarity = SliderRow("Clarity", -100, 100, 0)
        self.dehaze = SliderRow("Dehaze", 0, 100, 0)
        self.noise_reduction = SliderRow("Noise reduction", 0, 100, 0)
        for s in (self.sharpness, self.clarity, self.dehaze, self.noise_reduction):
            s.valueChanged.connect(lambda _: self.paramsChanged.emit())
            detail.add(s)
        v.addWidget(detail)

        v.addStretch(1)


class _ColorTab(QWidget):
    paramsChanged = Signal()
    presetChosen = Signal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(10)

        correction = SectionCard("COLOR CORRECTION")
        self.temperature = SliderRow("Temperature", -100, 100, 0)
        self.tint = SliderRow("Tint", -100, 100, 0)
        self.saturation = SliderRow("Saturation", -100, 100, 0)
        self.vibrance = SliderRow("Vibrance", -100, 100, 0)
        self.hue = SliderRow("Hue", -180, 180, 0)
        for s in (self.temperature, self.tint, self.saturation, self.vibrance, self.hue):
            s.valueChanged.connect(lambda _: self.paramsChanged.emit())
            correction.add(s)
        v.addWidget(correction)

        balance = SectionCard("COLOR BALANCE")
        self.red = SliderRow("Red", -100, 100, 0)
        self.green = SliderRow("Green", -100, 100, 0)
        self.blue = SliderRow("Blue", -100, 100, 0)
        for s in (self.red, self.green, self.blue):
            s.valueChanged.connect(lambda _: self.paramsChanged.emit())
            balance.add(s)
        v.addWidget(balance)

        self.presets = PresetGrid("LOOKS / PRESETS", COLOR_PRESETS)
        self.presets.presetChosen.connect(self.presetChosen)
        v.addWidget(self.presets)

        v.addStretch(1)


class _EffectsTab(QWidget):
    paramsChanged = Signal()
    presetChosen = Signal(str, dict)
    rotateRequested = Signal(int)
    flipRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(10)

        eff = SectionCard("EFFECTS")
        self.vignette = SliderRow("Vignette", -100, 100, 0)
        self.vignette_feather = SliderRow("Vignette feather", 0, 100, 50)
        self.grain = SliderRow("Grain", 0, 100, 0)
        self.blur = SliderRow("Blur", 0, 50, 0)
        self.glow = SliderRow("Glow", 0, 100, 0)
        self.bloom = SliderRow("Bloom", 0, 100, 0)
        self.fade = SliderRow("Fade", 0, 100, 0)
        for s in (
            self.vignette,
            self.vignette_feather,
            self.grain,
            self.blur,
            self.glow,
            self.bloom,
            self.fade,
        ):
            s.valueChanged.connect(lambda _: self.paramsChanged.emit())
            eff.add(s)
        v.addWidget(eff)

        geom = SectionCard("GEOMETRY")
        row = QHBoxLayout()
        row.setSpacing(6)
        self.btn_rot_l = QPushButton("Rotate L")
        self.btn_rot_r = QPushButton("Rotate R")
        self.btn_flip_h = QPushButton("Flip H")
        self.btn_flip_v = QPushButton("Flip V")
        for b in (self.btn_rot_l, self.btn_rot_r, self.btn_flip_h, self.btn_flip_v):
            b.setObjectName("Ghost")
            row.addWidget(b)
        geom.add_layout(row)
        v.addWidget(geom)

        self.presets = PresetGrid("CREATIVE FILTERS", EFFECT_PRESETS)
        self.presets.presetChosen.connect(self.presetChosen)
        v.addWidget(self.presets)

        v.addStretch(1)

        self.btn_rot_l.clicked.connect(lambda: self.rotateRequested.emit(-90))
        self.btn_rot_r.clicked.connect(lambda: self.rotateRequested.emit(90))
        self.btn_flip_h.clicked.connect(lambda: self.flipRequested.emit("h"))
        self.btn_flip_v.clicked.connect(lambda: self.flipRequested.emit("v"))


# ---------- Right panel ---------------------------------------------


class EditPanel(QFrame):
    """Stable right-side editing panel:
    ┌ brand ───────────────────────────┐
    │ Adjust  Color  Effects  Export   │  segmented tabs
    │ ┌──────────────────────────────┐ │
    │ │ (scrollable tab content)     │ │
    │ └──────────────────────────────┘ │
    │ Reset · Apply · Save             │  stable action bar
    └──────────────────────────────────┘
    """

    paramsChanged = Signal(EditParams)
    applyRequested = Signal()
    saveRequested = Signal()
    resetRequested = Signal()
    rotateRequested = Signal(int)
    flipRequested = Signal(str)
    saveCurrentRequested = Signal(object)  # ExportSettings
    saveAsRequested = Signal(object)
    batchExportRequested = Signal(object)
    tabChanged = Signal(int)

    TABS = ("Adjust", "Color", "Effects", "Export")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")
        # Enforce stable width so controls never collapse
        self.setMinimumWidth(340)
        self.setMaximumWidth(460)

        self._suspend = False

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # --- Brand header
        brand = QLabel(APP_NAME)
        brand.setObjectName("Brand")
        sub = QLabel(APP_TAGLINE)
        sub.setObjectName("BrandSub")
        root.addWidget(brand)
        root.addWidget(sub)

        # --- Segmented tab buttons
        tabs_row = QHBoxLayout()
        tabs_row.setSpacing(0)
        self._tab_group = QButtonGroup(self)
        self._tab_group.setExclusive(True)
        self._tab_buttons: list[QPushButton] = []
        for i, name in enumerate(self.TABS):
            b = QPushButton(name)
            b.setObjectName("Segment")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            if i == 0:
                b.setChecked(True)
            b.clicked.connect(lambda _c, idx=i: self._goto_tab(idx))
            self._tab_group.addButton(b, i)
            self._tab_buttons.append(b)
            tabs_row.addWidget(b)
        tabs_row.addStretch(1)
        root.addLayout(tabs_row)

        # --- Tab stack — each tab gets its OWN scroll area for isolation
        self._stack = QStackedWidget()

        self.adjust_tab = _AdjustTab()
        self.color_tab = _ColorTab()
        self.effects_tab = _EffectsTab()
        self.export_tab = ExportPanel()

        for body in (self.adjust_tab, self.color_tab, self.effects_tab, self.export_tab):
            scroll = QScrollArea()
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setWidget(body)
            self._stack.addWidget(scroll)
        root.addWidget(self._stack, 1)

        # --- Stable action bar
        action_bar = QFrame()
        action_bar.setObjectName("ActionBar")
        bar = QHBoxLayout(action_bar)
        bar.setContentsMargins(10, 8, 10, 8)
        bar.setSpacing(8)
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setObjectName("Ghost")
        self.btn_reset.setIcon(icon("reset"))
        self.btn_reset.setIconSize(QSize(16, 16))
        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setObjectName("Ghost")
        self.btn_save = QPushButton("Save")
        self.btn_save.setObjectName("Primary")
        self.btn_save.setIcon(icon("save"))
        self.btn_save.setIconSize(QSize(16, 16))
        bar.addWidget(self.btn_reset)
        bar.addWidget(self.btn_apply, 1)
        bar.addWidget(self.btn_save, 1)
        root.addWidget(action_bar)

        # --- Wiring
        for t in (self.adjust_tab, self.color_tab, self.effects_tab):
            t.paramsChanged.connect(self._emit_params)
        self.color_tab.presetChosen.connect(self._on_preset)
        self.effects_tab.presetChosen.connect(self._on_preset)
        self.effects_tab.rotateRequested.connect(self.rotateRequested)
        self.effects_tab.flipRequested.connect(self.flipRequested)

        self.btn_reset.clicked.connect(self.resetRequested)
        self.btn_apply.clicked.connect(self.applyRequested)
        self.btn_save.clicked.connect(self.saveRequested)

        self.export_tab.saveCurrentRequested.connect(self.saveCurrentRequested)
        self.export_tab.saveAsRequested.connect(self.saveAsRequested)
        self.export_tab.batchExportRequested.connect(self.batchExportRequested)

    # ---------- API --------------------------------------------------

    def goto_tab(self, index: int) -> None:
        if 0 <= index < len(self._tab_buttons):
            self._tab_buttons[index].setChecked(True)
            self._goto_tab(index)

    def _goto_tab(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        self.tabChanged.emit(index)

    def params(self) -> EditParams:
        a, c, e = self.adjust_tab, self.color_tab, self.effects_tab
        return EditParams(
            exposure=a.exposure.value(),
            brightness=a.brightness.value(),
            contrast=a.contrast.value(),
            highlights=a.highlights.value(),
            shadows=a.shadows.value(),
            whites=a.whites.value(),
            blacks=a.blacks.value(),
            sharpness=a.sharpness.value(),
            clarity=a.clarity.value(),
            dehaze=a.dehaze.value(),
            noise_reduction=a.noise_reduction.value(),
            saturation=c.saturation.value(),
            vibrance=c.vibrance.value(),
            temperature=c.temperature.value(),
            tint=c.tint.value(),
            hue=c.hue.value(),
            red=c.red.value(),
            green=c.green.value(),
            blue=c.blue.value(),
            vignette=e.vignette.value(),
            vignette_feather=e.vignette_feather.value(),
            grain=e.grain.value(),
            blur=e.blur.value(),
            glow=e.glow.value(),
            bloom=e.bloom.value(),
            fade=e.fade.value(),
        )

    def set_params(self, p: EditParams) -> None:
        self._suspend = True
        a, c, e = self.adjust_tab, self.color_tab, self.effects_tab
        a.exposure.set_value(p.exposure)
        a.brightness.set_value(p.brightness)
        a.contrast.set_value(p.contrast)
        a.highlights.set_value(p.highlights)
        a.shadows.set_value(p.shadows)
        a.whites.set_value(p.whites)
        a.blacks.set_value(p.blacks)
        a.sharpness.set_value(p.sharpness)
        a.clarity.set_value(p.clarity)
        a.dehaze.set_value(p.dehaze)
        a.noise_reduction.set_value(p.noise_reduction)
        c.saturation.set_value(p.saturation)
        c.vibrance.set_value(p.vibrance)
        c.temperature.set_value(p.temperature)
        c.tint.set_value(p.tint)
        c.hue.set_value(p.hue)
        c.red.set_value(p.red)
        c.green.set_value(p.green)
        c.blue.set_value(p.blue)
        e.vignette.set_value(p.vignette)
        e.vignette_feather.set_value(p.vignette_feather)
        e.grain.set_value(p.grain)
        e.blur.set_value(p.blur)
        e.glow.set_value(p.glow)
        e.bloom.set_value(p.bloom)
        e.fade.set_value(p.fade)
        self._suspend = False
        self._emit_params()

    def set_source_image(self, bgr) -> None:
        """Refresh preset thumbnails using the user's image."""
        self.color_tab.presets.set_source_image(bgr)
        self.effects_tab.presets.set_source_image(bgr)

    # ---------- internals -------------------------------------------

    def _on_preset(self, name: str, overrides: dict) -> None:
        base = self.params()
        merged = replace(base, **{k: v for k, v in overrides.items() if hasattr(base, k)})
        self.set_params(merged)

    def _emit_params(self) -> None:
        if self._suspend:
            return
        self.paramsChanged.emit(self.params())
