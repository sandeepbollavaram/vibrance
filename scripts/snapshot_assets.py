"""Compose a single image showing how your assets are wired in:
  - icon @ 64px (taskbar size)
  - icon @ 256px (desktop shortcut size)
  - splash screen at app-startup size
  - hero artwork from the docs site

Output: marketing_preview.png at the repo root.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QPainter, QPixmap  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)

    ico = QIcon(str(ROOT / "src" / "image_editor" / "resources" / "app.ico"))
    splash = QPixmap(str(ROOT / "src" / "image_editor" / "resources" / "splash.png"))
    hero = QPixmap(str(ROOT / "docs" / "hero.png"))

    W, H = 1280, 720
    canvas = QImage(W, H, QImage.Format_ARGB32)
    canvas.fill(QColor("#0A0E1A"))
    p = QPainter(canvas)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)

    # Background glow
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(90, 176, 255, 25))
    p.drawEllipse(-200, -200, 800, 800)
    p.setBrush(QColor(120, 90, 255, 18))
    p.drawEllipse(W - 600, H - 600, 800, 800)

    # Title
    p.setPen(QColor("#FFFFFF"))
    p.setFont(QFont("Segoe UI", 28, QFont.Bold))
    p.drawText(40, 70, "Vibrance — assets check")
    p.setPen(QColor("#8FA0BD"))
    p.setFont(QFont("Segoe UI", 11))
    p.drawText(40, 96, "Icon · Splash · Hero · all wired in from D:/picofvibrance/")

    # Icon row
    p.setPen(QColor("#5AB0FF"))
    p.setFont(QFont("Segoe UI", 9, QFont.Bold))
    p.drawText(40, 140, "ICON  ·  16 / 32 / 64 / 128 / 256 px frames in app.ico")

    icon_sizes = [16, 32, 64, 128, 256]
    x = 40
    for s in icon_sizes:
        pm = ico.pixmap(s, s)
        p.drawPixmap(x, 160, pm)
        p.setPen(QColor("#6B7896"))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(x, 160 + s + 14, f"{s}px")
        x += s + 24

    # Splash
    p.setPen(QColor("#5AB0FF"))
    p.setFont(QFont("Segoe UI", 9, QFont.Bold))
    p.drawText(40, 470, "SPLASH  ·  shown for ~900ms during app launch")
    sp = splash.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    p.drawPixmap(40, 485, sp)

    # Hero
    p.setPen(QColor("#5AB0FF"))
    p.drawText(320, 470, "DOCS HERO  ·  https://sandeepbollavaram.github.io/image_editor_python/")
    hp = hero.scaled(W - 360, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    p.drawPixmap(320, 485, hp)

    p.end()

    out = ROOT / "marketing_preview.png"
    canvas.save(str(out), "PNG")
    print(f"saved: {out}  ({W}x{H})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
