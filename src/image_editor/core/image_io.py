from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from image_editor.config import ExportOptions


class ImageIOError(Exception):
    pass


def load_image(path: str | Path) -> np.ndarray:
    """Load an image as BGR uint8. Uses numpy+imdecode so unicode paths work on Windows."""
    p = Path(path)
    if not p.is_file():
        raise ImageIOError(f"Not a file: {p}")
    data = np.fromfile(str(p), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ImageIOError(f"Failed to decode image: {p}")
    return img


def save_image(path: str | Path, image: np.ndarray, opts: ExportOptions | None = None) -> Path:
    """Save BGR uint8 image. Encode via imencode + tofile for unicode path safety."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    opts = opts or ExportOptions()
    ext = p.suffix.lower().lstrip(".") or opts.format
    params: list[int] = []
    if ext in ("jpg", "jpeg"):
        params = [cv2.IMWRITE_JPEG_QUALITY, int(opts.quality)]
    elif ext == "webp":
        params = [cv2.IMWRITE_WEBP_QUALITY, int(opts.quality)]
    elif ext == "png":
        # map quality 1..100 -> compression 9..0
        comp = max(0, min(9, 9 - int(opts.quality / 11)))
        params = [cv2.IMWRITE_PNG_COMPRESSION, comp]

    ok, buf = cv2.imencode(f".{ext}", image, params)
    if not ok:
        raise ImageIOError(f"Failed to encode image as .{ext}")
    buf.tofile(str(p))
    return p


def resize_long_edge(image: np.ndarray, long_edge: int) -> np.ndarray:
    if long_edge <= 0:
        return image
    h, w = image.shape[:2]
    if max(h, w) <= long_edge:
        return image
    scale = long_edge / max(h, w)
    return cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
