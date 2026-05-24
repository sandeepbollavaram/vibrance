"""Pure NumPy/OpenCV image filters. No Qt, no I/O.

All public functions take a BGR uint8 ``np.ndarray`` and return a BGR uint8 ``np.ndarray``.
Sliders use -100..100 (or 0..100 for unipolar). Internal math is float32 in 0..1 range
where possible to avoid clipping artifacts.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from image_editor.config import EditParams

# ----------------------------- helpers -----------------------------


def _to_float(img: np.ndarray) -> np.ndarray:
    return img.astype(np.float32) / 255.0


def _to_uint8(img: np.ndarray) -> np.ndarray:
    return np.clip(img * 255.0, 0, 255).astype(np.uint8)


# ----------------------------- tone -----------------------------


def brightness_contrast(img: np.ndarray, brightness: int, contrast: int) -> np.ndarray:
    if brightness == 0 and contrast == 0:
        return img
    alpha = 1.0 + contrast / 100.0
    beta = brightness  # -100..100 directly maps to byte offset
    return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)


def exposure(img: np.ndarray, value: int) -> np.ndarray:
    if value == 0:
        return img
    # Gamma-style exposure. Positive = brighter (gamma < 1 on inverted curve).
    gamma = max(0.05, 1.0 + value / 100.0)
    inv = 1.0 / gamma
    lut = np.array([((i / 255.0) ** inv) * 255 for i in range(256)]).astype(np.uint8)
    return cv2.LUT(img, lut)


def highlights_shadows(img: np.ndarray, highlights: int, shadows: int) -> np.ndarray:
    """Lift shadows / recover highlights via a soft luminance-masked offset."""
    if highlights == 0 and shadows == 0:
        return img
    f = _to_float(img)
    # luminance mask in 0..1
    lum = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    hi_mask = np.clip((lum - 0.5) * 2.0, 0, 1)[..., None]
    sh_mask = np.clip((0.5 - lum) * 2.0, 0, 1)[..., None]
    f = f + hi_mask * (highlights / 200.0)
    f = f + sh_mask * (shadows / 200.0)
    return _to_uint8(f)


def whites_blacks(img: np.ndarray, whites: int, blacks: int) -> np.ndarray:
    """Clip-style adjustments of the extreme top / bottom of the tonal range.
    `whites` shifts the white-point (>0 brightens whites further),
    `blacks` shifts the black-point (>0 lifts blacks toward gray).
    """
    if whites == 0 and blacks == 0:
        return img
    f = _to_float(img)
    lum = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    # Stronger masks at extremes only
    w_mask = np.clip((lum - 0.7) / 0.3, 0, 1)[..., None]
    b_mask = np.clip((0.3 - lum) / 0.3, 0, 1)[..., None]
    f = f + w_mask * (whites / 200.0)
    f = f + b_mask * (blacks / 200.0)
    return _to_uint8(f)


def clarity(img: np.ndarray, amount: int) -> np.ndarray:
    """Midtone local contrast (unsharp at a wide radius)."""
    if amount == 0:
        return img
    strength = amount / 100.0
    blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=10)
    return cv2.addWeighted(img, 1.0 + strength * 0.5, blurred, -strength * 0.5, 0)


def dehaze(img: np.ndarray, amount: int) -> np.ndarray:
    """Lightweight dehaze: estimate the airlight as the brightest blurred pixels
    and subtract a fraction of it, then re-stretch contrast."""
    if amount <= 0:
        return img
    f = _to_float(img)
    # crude airlight estimate
    blurred = cv2.GaussianBlur(f, (0, 0), sigmaX=12)
    airlight = np.percentile(blurred.reshape(-1, 3), 99.5, axis=0)
    a = amount / 100.0 * 0.6  # cap effect
    transmission = np.clip(1.0 - a * (blurred / np.maximum(airlight, 1e-3)), 0.25, 1.0)
    out = (f - airlight) / transmission + airlight
    return _to_uint8(out)


# ----------------------------- color -----------------------------


def saturation_vibrance(img: np.ndarray, saturation: int, vibrance: int) -> np.ndarray:
    if saturation == 0 and vibrance == 0:
        return img
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    s = hsv[..., 1] / 255.0
    if saturation != 0:
        s = s * (1.0 + saturation / 100.0)
    if vibrance != 0:
        # vibrance boosts less-saturated pixels more
        boost = (vibrance / 100.0) * (1.0 - s)
        s = s + boost
    hsv[..., 1] = np.clip(s * 255.0, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def hue_shift(img: np.ndarray, degrees: int) -> np.ndarray:
    """Rotate the hue circle by ``degrees`` in -180..180."""
    if degrees == 0:
        return img
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.int16)
    hsv[..., 0] = (hsv[..., 0] + int(degrees / 2)) % 180  # OpenCV H is 0..179
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def channel_mixer(img: np.ndarray, red: int, green: int, blue: int) -> np.ndarray:
    """Per-channel offset, -100..100 mapping to +/- 64 byte units."""
    if red == 0 and green == 0 and blue == 0:
        return img
    out = img.astype(np.int16)
    out[..., 0] += int(blue * 0.64)
    out[..., 1] += int(green * 0.64)
    out[..., 2] += int(red * 0.64)
    return np.clip(out, 0, 255).astype(np.uint8)


def temperature_tint(img: np.ndarray, temperature: int, tint: int) -> np.ndarray:
    if temperature == 0 and tint == 0:
        return img
    f = _to_float(img)
    # BGR layout: B=cool, R=warm; G shifts on tint.
    t = temperature / 200.0
    g = tint / 200.0
    f[..., 0] = f[..., 0] - t  # B
    f[..., 2] = f[..., 2] + t  # R
    f[..., 1] = f[..., 1] - g  # G (negative tint = greener)
    return _to_uint8(f)


# ----------------------------- detail -----------------------------


def gaussian_blur(img: np.ndarray, amount: int) -> np.ndarray:
    if amount <= 0:
        return img
    k = amount * 2 + 1
    return cv2.GaussianBlur(img, (k, k), 0)


def unsharp_sharpen(img: np.ndarray, amount: int) -> np.ndarray:
    if amount <= 0:
        return img
    strength = amount / 100.0
    blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=1.5)
    return cv2.addWeighted(img, 1.0 + strength, blurred, -strength, 0)


# ----------------------------- geometry -----------------------------


def rotate_flip(img: np.ndarray, rotate: int, flip_h: bool, flip_v: bool) -> np.ndarray:
    out = img
    if rotate == 90:
        out = cv2.rotate(out, cv2.ROTATE_90_CLOCKWISE)
    elif rotate == 180:
        out = cv2.rotate(out, cv2.ROTATE_180)
    elif rotate == 270:
        out = cv2.rotate(out, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if flip_h:
        out = cv2.flip(out, 1)
    if flip_v:
        out = cv2.flip(out, 0)
    return out


# ----------------------------- LUT -----------------------------


def apply_cube_lut(img: np.ndarray, lut_path: str) -> np.ndarray:
    p = Path(lut_path)
    if not lut_path or not p.is_file():
        return img
    lut = _parse_cube_lut(p)
    if lut is None:
        return img
    return _apply_3d_lut(img, lut)


def _parse_cube_lut(path: Path) -> np.ndarray | None:
    size = None
    rows: list[tuple[float, float, float]] = []
    try:
        for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.upper().startswith("LUT_3D_SIZE"):
                size = int(line.split()[-1])
                continue
            if line[0].isalpha():
                continue
            parts = line.split()
            if len(parts) >= 3:
                rows.append((float(parts[0]), float(parts[1]), float(parts[2])))
    except Exception:
        return None
    if not size or len(rows) != size**3:
        return None
    arr = np.array(rows, dtype=np.float32).reshape(size, size, size, 3)
    return arr  # axes: r, g, b (cube convention)


def _apply_3d_lut(img_bgr: np.ndarray, lut: np.ndarray) -> np.ndarray:
    size = lut.shape[0]
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    idx = rgb * (size - 1)
    i0 = np.floor(idx).astype(np.int32)
    i1 = np.clip(i0 + 1, 0, size - 1)
    f = idx - i0

    r0, g0, b0 = i0[..., 0], i0[..., 1], i0[..., 2]
    r1, g1, b1 = i1[..., 0], i1[..., 1], i1[..., 2]
    fr, fg, fb = f[..., 0:1], f[..., 1:2], f[..., 2:3]

    def L(r, g, b):  # noqa: E743
        return lut[r, g, b]

    c000 = L(r0, g0, b0)
    c100 = L(r1, g0, b0)
    c010 = L(r0, g1, b0)
    c110 = L(r1, g1, b0)
    c001 = L(r0, g0, b1)
    c101 = L(r1, g0, b1)
    c011 = L(r0, g1, b1)
    c111 = L(r1, g1, b1)

    c00 = c000 * (1 - fr) + c100 * fr
    c10 = c010 * (1 - fr) + c110 * fr
    c01 = c001 * (1 - fr) + c101 * fr
    c11 = c011 * (1 - fr) + c111 * fr
    c0 = c00 * (1 - fg) + c10 * fg
    c1 = c01 * (1 - fg) + c11 * fg
    out = c0 * (1 - fb) + c1 * fb

    out = np.clip(out * 255.0, 0, 255).astype(np.uint8)
    return cv2.cvtColor(out, cv2.COLOR_RGB2BGR)


# ----------------------------- effects -----------------------------


def vignette(img: np.ndarray, amount: int, feather: int = 50) -> np.ndarray:
    """Radial darken (positive amount) or brighten (negative) toward edges."""
    if amount == 0:
        return img
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cy, cx = h / 2.0, w / 2.0
    dist = np.sqrt(((yy - cy) / cy) ** 2 + ((xx - cx) / cx) ** 2)
    f = max(0.05, feather / 100.0)
    mask = np.clip((dist - (1.0 - f)) / f, 0.0, 1.0)
    strength = amount / 100.0
    factor = 1.0 - mask * strength  # >1 brightens, <1 darkens
    out = img.astype(np.float32) * factor[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def film_grain(img: np.ndarray, amount: int, seed: int = 0) -> np.ndarray:
    """Monochromatic Gaussian noise added on top of the image."""
    if amount <= 0:
        return img
    rng = np.random.default_rng(seed)
    sigma = amount / 100.0 * 24.0
    noise = rng.normal(0, sigma, img.shape[:2]).astype(np.float32)
    out = img.astype(np.float32) + noise[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def denoise(img: np.ndarray, amount: int) -> np.ndarray:
    """Fast non-local-means colour denoise. Strength scales with amount."""
    if amount <= 0:
        return img
    h = amount / 100.0 * 15.0
    return cv2.fastNlMeansDenoisingColored(img, None, h, h, 7, 21)


def glow(img: np.ndarray, amount: int) -> np.ndarray:
    """Orton-style soft glow: blend the image with its blurred copy."""
    if amount <= 0:
        return img
    blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=15)
    a = amount / 100.0 * 0.6
    return cv2.addWeighted(img, 1.0 - a, blurred, a, 0)


def bloom(img: np.ndarray, amount: int) -> np.ndarray:
    """Threshold the brightest pixels, blur them, screen-blend back."""
    if amount <= 0:
        return img
    f = _to_float(img)
    gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    mask = np.clip((gray - 0.75) * 4.0, 0, 1)[..., None]
    highlights = f * mask
    halo = cv2.GaussianBlur(highlights, (0, 0), sigmaX=18)
    a = amount / 100.0 * 0.8
    out = 1.0 - (1.0 - f) * (1.0 - halo * a)  # screen blend
    return _to_uint8(out)


def fade(img: np.ndarray, amount: int) -> np.ndarray:
    """Matte / film fade: lift blacks toward mid-gray. 0 = no effect."""
    if amount <= 0:
        return img
    a = amount / 100.0
    lift = 0.18 * a  # how high blacks rise (0..1)
    f = _to_float(img)
    out = f * (1.0 - lift) + lift
    return _to_uint8(out)


def color_grade(
    img: np.ndarray,
    shadows: tuple[float, float],
    mids: tuple[float, float],
    highs: tuple[float, float],
) -> np.ndarray:
    """3-way color grading. Each input is (dx, dy) in -1..1 from the wheel.

    dx maps to a/b shift in Lab; we use a simple BGR offset weighted by luminance
    masks so shadows-mid-highs each affect only their tonal range. This is the
    classic "color wheel" approach used in editors.
    """
    if shadows == (0, 0) and mids == (0, 0) and highs == (0, 0):
        return img
    f = _to_float(img)
    lum = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    sh_mask = np.clip(1.0 - lum * 2.0, 0, 1)[..., None]
    hi_mask = np.clip((lum - 0.5) * 2.0, 0, 1)[..., None]
    mid_mask = np.clip(1.0 - np.abs(lum - 0.5) * 2.0, 0, 1)[..., None]

    def _shift(target: np.ndarray, mask: np.ndarray, dxdy: tuple[float, float]) -> np.ndarray:
        dx, dy = dxdy
        # dx = warm/cool axis -> R - B, dy = green/magenta -> G shift
        delta_b = -dx * 0.25
        delta_r = dx * 0.25
        delta_g = -dy * 0.25
        adj = np.zeros_like(target)
        adj[..., 0] = delta_b
        adj[..., 1] = delta_g
        adj[..., 2] = delta_r
        return target + adj * mask

    out = _shift(f, sh_mask, shadows)
    out = _shift(out, mid_mask, mids)
    out = _shift(out, hi_mask, highs)
    return _to_uint8(out)


def apply_curve(img: np.ndarray, points: list[tuple[float, float]] | None) -> np.ndarray:
    """Apply an RGB curve. ``points`` are (x, y) in 0..1; the curve is built
    via piecewise-linear interpolation and applied as a single 256-entry LUT."""
    if not points or len(points) < 2:
        return img
    pts = sorted(points)
    xs = np.array([p[0] for p in pts]) * 255.0
    ys = np.array([p[1] for p in pts]) * 255.0
    lut = np.interp(np.arange(256), xs, ys)
    lut = np.clip(lut, 0, 255).astype(np.uint8)
    return cv2.LUT(img, lut)


# ----------------------------- pipeline -----------------------------


def apply_all(img: np.ndarray, p: EditParams) -> np.ndarray:
    """Apply every parameter in canonical order:
    geometry -> light -> tone -> color -> grading -> curves -> detail -> effects -> LUT."""
    if p.is_identity():
        return img
    out = rotate_flip(img, p.rotate, p.flip_h, p.flip_v)

    # Light & tone
    out = exposure(out, p.exposure)
    out = brightness_contrast(out, p.brightness, p.contrast)
    out = highlights_shadows(out, p.highlights, p.shadows)
    out = whites_blacks(out, p.whites, p.blacks)

    # Color
    out = saturation_vibrance(out, p.saturation, p.vibrance)
    out = temperature_tint(out, p.temperature, p.tint)
    out = hue_shift(out, p.hue)
    out = channel_mixer(out, p.red, p.green, p.blue)
    out = color_grade(out, p.grade_shadows, p.grade_mids, p.grade_highs)

    # Curves
    out = apply_curve(out, p.curve_rgb)

    # Detail
    if p.noise_reduction > 0:
        out = denoise(out, p.noise_reduction)
    out = dehaze(out, p.dehaze)
    out = clarity(out, p.clarity)
    out = gaussian_blur(out, p.blur)
    out = unsharp_sharpen(out, p.sharpness if p.sharpness > 0 else 0)

    # Effects
    out = glow(out, p.glow)
    out = bloom(out, p.bloom)
    out = fade(out, p.fade)
    out = vignette(out, p.vignette, p.vignette_feather)
    if p.grain > 0:
        out = film_grain(out, p.grain)
    if p.lut_path:
        out = apply_cube_lut(out, p.lut_path)
    return out


# ----------------------------- spot heal -----------------------------


def spot_heal(img: np.ndarray, mask: np.ndarray, radius: int = 6) -> np.ndarray:
    """Classical inpainting (Telea). ``mask`` is a uint8 array where >0 marks
    pixels to repair. Not ML — just neighborhood interpolation."""
    if mask is None or mask.max() == 0:
        return img
    if mask.dtype != np.uint8:
        mask = mask.astype(np.uint8)
    return cv2.inpaint(img, mask, radius, cv2.INPAINT_TELEA)


# ----------------------------- histogram -----------------------------


def histogram(img: np.ndarray) -> dict[str, np.ndarray]:
    """Return per-channel + luminance histograms (256 bins, int32)."""
    chans = cv2.split(img)  # B G R
    b = cv2.calcHist([chans[0]], [0], None, [256], [0, 256]).flatten().astype(np.int32)
    g = cv2.calcHist([chans[1]], [0], None, [256], [0, 256]).flatten().astype(np.int32)
    r = cv2.calcHist([chans[2]], [0], None, [256], [0, 256]).flatten().astype(np.int32)
    lum = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    y = cv2.calcHist([lum], [0], None, [256], [0, 256]).flatten().astype(np.int32)
    return {"r": r, "g": g, "b": b, "y": y}
