import numpy as np

from image_editor.core.compress import compress_quality, compress_to_size, save_compressed


def _photo(h=400, w=600):
    """Realistic photo-like image: smooth gradients + low-amplitude noise.

    Pure random noise is the JPEG worst case and never compresses below ~100 KB
    even at quality=30. Real photos compress 10–20× better, so the fixture
    needs to be photo-like for size-target tests to be meaningful.
    """
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    b = (xx / w * 200 + 30)
    g = (np.sin(yy / 30.0) * 60 + 130)
    r = (yy / h * 220 + 20)
    img = np.dstack([b, g, r])
    rng = np.random.default_rng(42)
    img = img + rng.normal(0, 5, img.shape)
    return np.clip(img, 0, 255).astype(np.uint8)


def test_compress_quality_returns_bytes():
    r = compress_quality(_photo(), fmt="jpg", quality=80)
    assert isinstance(r.bytes_out, bytes) and len(r.bytes_out) > 0
    assert r.quality_used == 80


def test_compress_to_size_hits_target():
    img = _photo(600, 800)
    r = compress_to_size(img, target_kb=80, fmt="jpg")
    # JPEG is approximate; allow 30% slack above target before failing the test.
    assert r.size_kb <= 80 * 1.3, f"got {r.size_kb} KB"
    assert 30 <= r.quality_used <= 95


def test_save_compressed_writes_file(tmp_path):
    img = _photo()
    out = tmp_path / "x.jpg"
    r = save_compressed(out, img, target_kb=50, fmt="jpg")
    assert out.is_file() and out.stat().st_size > 0
    assert abs(out.stat().st_size / 1024 - r.size_kb) < 1


def test_compress_resizes_when_max_long_edge():
    img = _photo(800, 1200)
    r = compress_quality(img, fmt="jpg", quality=85, max_long_edge=600)
    assert max(r.width, r.height) == 600
