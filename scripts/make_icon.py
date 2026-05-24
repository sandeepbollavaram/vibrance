"""Generate ``src/image_editor/resources/app.ico`` from a source PNG.

Lookup order for the source:
    1. CLI arg:  python scripts/make_icon.py path/to/your.png
    2. ``vibrance.png`` at the repo root (your real artwork)
    3. ``D:/picofvibrance/vibrance.png`` (the directory you delivered)
    4. Fallback: synthesize a minimal placeholder

The .ico contains 16/24/32/48/64/128/256 px frames so Windows picks the right
size for the desktop shortcut, taskbar, Start menu, and the EXE.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ICO_OUT = ROOT / "src" / "image_editor" / "resources" / "app.ico"
SMALL_PNG_OUT = ROOT / "docs" / "app.png"   # favicon-sized export for the docs site

SIZES = [16, 24, 32, 48, 64, 128, 256]


def _find_source(argv: list[str]) -> Path | None:
    if len(argv) > 1:
        p = Path(argv[1])
        if p.is_file():
            return p
    candidates = [
        ROOT / "vibrance.png",
        Path("D:/picofvibrance/vibrance.png"),
        ROOT / "docs" / "vibrance.png",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def _placeholder(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = max(1, size // 32)
    d.rounded_rectangle(
        (pad, pad, size - pad, size - pad),
        radius=int(size * 0.22),
        fill=(15, 17, 21, 255),
        outline=(35, 41, 52, 255),
        width=max(1, size // 64),
    )
    cx, cy = size / 2, size / 2 - size * 0.04
    s = size * 0.28
    pts = [(cx - s, cy - s * 0.8), (cx, cy + s * 0.9), (cx + s, cy - s * 0.8)]
    d.line([pts[0], pts[1]], fill=(90, 176, 255, 255), width=max(2, size // 12))
    d.line([pts[1], pts[2]], fill=(255, 255, 255, 255), width=max(2, size // 12))
    dot_r = max(1, size // 20)
    d.ellipse(
        (cx + s - dot_r, cy - s * 0.8 - dot_r, cx + s + dot_r, cy - s * 0.8 + dot_r),
        fill=(90, 176, 255, 255),
    )
    return img


def _resize_from_source(src: Image.Image, size: int) -> Image.Image:
    """Square-crop and high-quality resize the source PNG to ``size``."""
    img = src.convert("RGBA")
    w, h = img.size
    side = min(w, h)
    img = img.crop(((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2))
    return img.resize((size, size), Image.LANCZOS)


def main() -> int:
    src_path = _find_source(sys.argv)
    if src_path:
        print(f"source: {src_path}")
        src = Image.open(src_path)
        frames = [_resize_from_source(src, s) for s in SIZES]
    else:
        print("source: <placeholder>  (no PNG found; using synthesized fallback)")
        frames = [_placeholder(s) for s in SIZES]

    ICO_OUT.parent.mkdir(parents=True, exist_ok=True)
    SMALL_PNG_OUT.parent.mkdir(parents=True, exist_ok=True)

    # ICO multi-resolution
    frames[-1].save(ICO_OUT, format="ICO", sizes=[(s, s) for s in SIZES])
    # Docs favicon (32px PNG)
    frames[SIZES.index(32)].save(SMALL_PNG_OUT, format="PNG")

    print(f"wrote {ICO_OUT}  ({ICO_OUT.stat().st_size} bytes)")
    print(f"wrote {SMALL_PNG_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
