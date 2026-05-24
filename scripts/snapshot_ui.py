"""Render Vibrance offscreen with a synthetic image and capture a screenshot.

Used for headless UI verification on machines without a display. The output
goes to ``screenshot.png`` at the repo root.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from PySide6.QtCore import QSize  # noqa: E402
from PySide6.QtGui import QPixmap  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from image_editor.config import EditParams  # noqa: E402
from image_editor.ui.main_window import MainWindow  # noqa: E402
from image_editor.ui.theme import apply_dark_theme  # noqa: E402


def make_sample(h: int = 720, w: int = 1080) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    b = (xx / w * 220 + 20).astype(np.uint8)
    g = ((np.sin(yy / 80.0) + 1) * 110 + 30).astype(np.uint8)
    r = (yy / h * 230 + 20).astype(np.uint8)
    img = np.dstack([b, g, r])
    cy, cx = h / 2, w / 2
    dist = np.sqrt(((yy - cy) / cy) ** 2 + ((xx - cx) / cx) ** 2)
    vignette = np.clip(1.0 - dist * 0.55, 0.35, 1.0).astype(np.float32)[..., None]
    img = (img.astype(np.float32) * vignette).clip(0, 255).astype(np.uint8)
    cv2.putText(img, "VIBRANCE", (40, h - 50), cv2.FONT_HERSHEY_DUPLEX,
                1.8, (255, 255, 255), 3, cv2.LINE_AA)
    return img


def main() -> int:
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    w = MainWindow()
    w.resize(QSize(1680, 980))

    sample = make_sample()
    w._current_image = sample
    w._current_path = "synthetic.png"
    w.canvas_stack.setCurrentIndex(1)
    w.edit_panel.set_params(
        EditParams(
            exposure=6, contrast=18, saturation=18, vibrance=15,
            highlights=-10, shadows=14, clarity=14, sharpness=22,
            vignette=22, vignette_feather=55, fade=10,
        )
    )
    w._render_preview(force=True)
    w._refresh_thumbnails()
    w.statusBar().showMessage("synthetic.png  ·  1080×720  ·  preset: Cinema")

    w.show()
    app.processEvents(); app.processEvents(); app.processEvents()

    pix: QPixmap = w.grab()
    out = ROOT / "screenshot.png"
    pix.save(str(out), "PNG")
    print(f"saved: {out}  ({pix.width()}x{pix.height()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
