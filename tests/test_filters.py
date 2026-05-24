import numpy as np
import pytest

from image_editor.config import EditParams
from image_editor.core import filters


@pytest.fixture
def gradient() -> np.ndarray:
    """A 64x64 BGR gradient image."""
    x = np.linspace(0, 255, 64, dtype=np.uint8)
    band = np.tile(x, (64, 1))
    return np.dstack([band, band, band])


def test_identity_returns_same(gradient):
    out = filters.apply_all(gradient, EditParams())
    assert out is gradient or np.array_equal(out, gradient)


def test_brightness_increases_mean(gradient):
    out = filters.brightness_contrast(gradient, brightness=50, contrast=0)
    assert out.mean() > gradient.mean()


def test_contrast_changes_std(gradient):
    out = filters.brightness_contrast(gradient, brightness=0, contrast=80)
    assert out.std() >= gradient.std()


def test_blur_reduces_std(gradient):
    out = filters.gaussian_blur(gradient, amount=10)
    assert out.std() < gradient.std() + 1e-6


def test_sharpen_keeps_shape(gradient):
    out = filters.unsharp_sharpen(gradient, amount=50)
    assert out.shape == gradient.shape
    assert out.dtype == np.uint8


def test_rotate_90_swaps_dims(gradient):
    out = filters.rotate_flip(gradient, rotate=90, flip_h=False, flip_v=False)
    assert out.shape[:2] == gradient.shape[:2][::-1]


def test_apply_all_keeps_dtype_and_shape(gradient):
    params = EditParams(
        brightness=10,
        contrast=10,
        exposure=5,
        highlights=20,
        shadows=20,
        saturation=15,
        vibrance=15,
        temperature=10,
        tint=-10,
        blur=2,
        sharpness=20,
    )
    out = filters.apply_all(gradient, params)
    assert out.shape == gradient.shape
    assert out.dtype == np.uint8


def test_histogram_sums_to_pixel_count(gradient):
    h = filters.histogram(gradient)
    total = gradient.shape[0] * gradient.shape[1]
    for key in ("r", "g", "b", "y"):
        assert int(h[key].sum()) == total


def test_vignette_darkens_corners(gradient):
    out = filters.vignette(gradient, amount=80, feather=50)
    h, w = gradient.shape[:2]
    corner = out[0, 0].astype(int).sum()
    center = out[h // 2, w // 2].astype(int).sum()
    assert corner < center


def test_vignette_zero_amount_is_noop(gradient):
    out = filters.vignette(gradient, amount=0)
    assert np.array_equal(out, gradient)


def test_film_grain_changes_image(gradient):
    out = filters.film_grain(gradient, amount=50, seed=1)
    assert out.shape == gradient.shape
    # With grain, the per-pixel diff should be non-zero somewhere.
    assert int(np.abs(out.astype(int) - gradient.astype(int)).sum()) > 0


def test_film_grain_zero_is_noop(gradient):
    assert np.array_equal(filters.film_grain(gradient, 0), gradient)


def test_color_grade_zero_is_noop(gradient):
    out = filters.color_grade(gradient, (0, 0), (0, 0), (0, 0))
    assert np.array_equal(out, gradient)


def test_color_grade_changes_image(gradient):
    out = filters.color_grade(gradient, (0.3, 0.0), (0.0, 0.0), (-0.2, 0.1))
    assert out.shape == gradient.shape
    assert not np.array_equal(out, gradient)


def test_apply_curve_identity_unchanged(gradient):
    out = filters.apply_curve(gradient, [(0.0, 0.0), (1.0, 1.0)])
    assert np.array_equal(out, gradient)


def test_apply_curve_inversion():
    img = np.array([[0, 128, 255]], dtype=np.uint8).reshape(1, 3, 1).repeat(3, axis=2)
    out = filters.apply_curve(img, [(0.0, 1.0), (1.0, 0.0)])
    # Inverted: 0->255, 255->0
    assert out[0, 0, 0] == 255
    assert out[0, 2, 0] == 0


def test_spot_heal_returns_image(gradient):
    mask = np.zeros(gradient.shape[:2], dtype=np.uint8)
    mask[10:30, 10:30] = 255
    out = filters.spot_heal(gradient, mask, radius=6)
    assert out.shape == gradient.shape
    assert out.dtype == np.uint8


def test_apply_all_with_new_params(gradient):
    params = EditParams(
        exposure=10,
        contrast=10,
        vignette=30,
        grain=10,
        noise_reduction=0,
        grade_shadows=(0.2, 0.0),
        grade_highs=(-0.1, 0.05),
        curve_rgb=[(0.0, 0.05), (0.5, 0.55), (1.0, 1.0)],
    )
    out = filters.apply_all(gradient, params)
    assert out.shape == gradient.shape
    assert out.dtype == np.uint8
