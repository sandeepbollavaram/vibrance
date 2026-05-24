"""Image compression: target-size encoding, metadata stripping, format conversion.

Two modes:
    1. ``compress_to_size`` — binary-search JPEG/WebP quality until the encoded
       byte length lands at or just under a target KB ceiling.
    2. ``compress_quality`` — direct quality-based encode (fast path).

All functions return ``bytes`` so callers control whether the result goes to
disk, memory, or a network stream.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from image_editor.core.image_io import resize_long_edge


@dataclass
class CompressionResult:
    bytes_out: bytes
    quality_used: int
    size_kb: float
    width: int
    height: int


def _encode(img: np.ndarray, fmt: str, quality: int) -> bytes:
    fmt = fmt.lower().lstrip(".")
    params: list[int] = []
    if fmt in ("jpg", "jpeg"):
        params = [cv2.IMWRITE_JPEG_QUALITY, int(quality),
                  cv2.IMWRITE_JPEG_OPTIMIZE, 1,
                  cv2.IMWRITE_JPEG_PROGRESSIVE, 1]
    elif fmt == "webp":
        params = [cv2.IMWRITE_WEBP_QUALITY, int(quality)]
    elif fmt == "png":
        comp = max(0, min(9, 9 - int(quality / 11)))
        params = [cv2.IMWRITE_PNG_COMPRESSION, comp]
    ok, buf = cv2.imencode(f".{fmt}", img, params)
    if not ok:
        raise ValueError(f"Encoder failed for .{fmt}")
    return buf.tobytes()


def compress_quality(
    img: np.ndarray, fmt: str = "jpg", quality: int = 85, max_long_edge: int = 0
) -> CompressionResult:
    """Encode once at the given quality. Optionally downscale first."""
    work = resize_long_edge(img, max_long_edge) if max_long_edge > 0 else img
    data = _encode(work, fmt, quality)
    return CompressionResult(
        bytes_out=data,
        quality_used=quality,
        size_kb=len(data) / 1024,
        width=work.shape[1],
        height=work.shape[0],
    )


def compress_to_size(
    img: np.ndarray,
    target_kb: float,
    fmt: str = "jpg",
    max_long_edge: int = 0,
    min_quality: int = 30,
    max_quality: int = 95,
) -> CompressionResult:
    """Binary-search the encoder quality to hit ``target_kb`` (or just under).

    Falls back to the lowest tested quality if even ``min_quality`` overshoots.
    PNG ignores quality meaningfully, so for PNG we just use ``compress_quality``
    with the average. Use jpg or webp for genuine size targeting.
    """
    if target_kb <= 0:
        raise ValueError("target_kb must be > 0")

    work = resize_long_edge(img, max_long_edge) if max_long_edge > 0 else img
    lo, hi = min_quality, max_quality
    best: CompressionResult | None = None

    while lo <= hi:
        mid = (lo + hi) // 2
        data = _encode(work, fmt, mid)
        size_kb = len(data) / 1024
        candidate = CompressionResult(data, mid, size_kb, work.shape[1], work.shape[0])

        if size_kb <= target_kb:
            best = candidate     # fits — try to go higher quality
            lo = mid + 1
        else:
            hi = mid - 1         # too big — drop quality

    if best is None:
        # Even the lowest quality overshot. Return that as the best effort.
        data = _encode(work, fmt, min_quality)
        best = CompressionResult(
            data, min_quality, len(data) / 1024, work.shape[1], work.shape[0]
        )
    return best


def strip_metadata(path: str | Path) -> None:
    """Re-encode a JPEG/PNG without EXIF/XMP/ICC chunks. Uses Pillow."""
    try:
        from PIL import Image
    except ImportError:
        return
    p = Path(path)
    with Image.open(p) as im:
        data = list(im.getdata())
        clean = Image.new(im.mode, im.size)
        clean.putdata(data)
        clean.save(p)


def save_compressed(
    path: str | Path,
    img: np.ndarray,
    *,
    target_kb: float | None = None,
    quality: int = 85,
    fmt: str | None = None,
    max_long_edge: int = 0,
) -> CompressionResult:
    """Encode and write in one call. Output format derived from ``path`` if not given."""
    p = Path(path)
    fmt = (fmt or p.suffix.lstrip(".")).lower()
    if target_kb is not None and target_kb > 0:
        result = compress_to_size(img, target_kb, fmt=fmt, max_long_edge=max_long_edge)
    else:
        result = compress_quality(img, fmt=fmt, quality=quality, max_long_edge=max_long_edge)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(result.bytes_out)
    return result
