from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

APP_NAME = "Vibrance"
APP_TAGLINE = "Photo editor, batch processor, compressor."
APP_ORG = "sandeepbollavaram"
APP_ID = "vibrance"
APP_GITHUB = "https://github.com/sandeepbollavaram/vibrance"

SUPPORTED_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp")

OUTPUT_SUBDIR = "edited"
LOG_DIR_NAME = "logs"
PRESETS_DIR_NAME = "presets"


def user_data_dir() -> Path:
    """Per-user app data directory (cross-platform)."""
    import os
    import sys

    if sys.platform.startswith("win"):
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    p = root / APP_ID
    p.mkdir(parents=True, exist_ok=True)
    return p


@dataclass
class EditParams:
    """Snapshot of every adjustable parameter. Pure data — no Qt."""

    # Light
    brightness: int = 0  # -100..100
    contrast: int = 0  # -100..100
    exposure: int = 0  # -100..100 (gamma-style)
    highlights: int = 0  # -100..100
    shadows: int = 0  # -100..100
    whites: int = 0  # -100..100  (lift / crush highlights only)
    blacks: int = 0  # -100..100  (lift / crush shadows only)

    # Detail
    sharpness: int = 0  # 0..100   (unsharp mask)
    clarity: int = 0  # -100..100 (midtone local contrast)
    dehaze: int = 0  # 0..100   (atmospheric scatter removal)
    noise_reduction: int = 0  # 0..100

    # Color correction
    saturation: int = 0  # -100..100
    vibrance: int = 0  # -100..100
    temperature: int = 0  # -100..100
    tint: int = 0  # -100..100
    hue: int = 0  # -180..180 (degree rotate)

    # Color balance (RGB channel mixer)
    red: int = 0  # -100..100
    green: int = 0  # -100..100
    blue: int = 0  # -100..100

    # 3-way color grading wheels (kept; not exposed in default UI but supported)
    grade_shadows: tuple[float, float] = (0.0, 0.0)
    grade_mids: tuple[float, float] = (0.0, 0.0)
    grade_highs: tuple[float, float] = (0.0, 0.0)

    # Effects
    blur: int = 0  # 0..50
    grain: int = 0  # 0..100
    glow: int = 0  # 0..100   (orton-lite soft glow)
    bloom: int = 0  # 0..100   (bright pixel halo)
    fade: int = 0  # 0..100   (lift blacks for matte film look)
    vignette: int = 0  # -100..100
    vignette_feather: int = 50  # 0..100

    # Curves: list of (x,y) control points in 0..1. None = identity.
    curve_rgb: list[tuple[float, float]] | None = None

    # Geometry
    rotate: int = 0  # 0/90/180/270
    flip_h: bool = False
    flip_v: bool = False

    # LUT
    lut_path: str = ""

    def is_identity(self) -> bool:
        return self == EditParams()


@dataclass
class ExportOptions:
    format: str = "jpg"  # jpg|png|webp|tiff
    quality: int = 92  # 1..100 (jpg/webp)
    resize_long_edge: int = 0  # 0 = no resize
    output_dir: str = ""  # empty = source/edited
    suffix: str = "_edited"
    preserve_exif: bool = True
