import numpy as np
import pytest

from image_editor.config import ExportOptions
from image_editor.core.image_io import ImageIOError, load_image, resize_long_edge, save_image


def test_save_and_load_roundtrip(tmp_path):
    img = (np.random.rand(40, 60, 3) * 255).astype(np.uint8)
    path = tmp_path / "sample.png"
    save_image(path, img)
    back = load_image(path)
    assert back.shape == img.shape


def test_load_missing_raises(tmp_path):
    with pytest.raises(ImageIOError):
        load_image(tmp_path / "nope.png")


def test_resize_long_edge_noop_when_smaller():
    img = np.zeros((10, 20, 3), dtype=np.uint8)
    out = resize_long_edge(img, 100)
    assert out.shape == img.shape


def test_resize_long_edge_scales():
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    out = resize_long_edge(img, 100)
    assert max(out.shape[:2]) == 100


def test_jpeg_quality_param(tmp_path):
    img = (np.random.rand(20, 20, 3) * 255).astype(np.uint8)
    path = tmp_path / "q.jpg"
    save_image(path, img, ExportOptions(format="jpg", quality=50))
    assert path.is_file() and path.stat().st_size > 0
