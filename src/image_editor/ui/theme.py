from __future__ import annotations

from importlib import resources

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

ACCENT = "#5AB0FF"
BG = "#0F1115"
PANEL = "#161A21"
TEXT = "#E6E8EB"
MUTED = "#8B95A3"


def apply_dark_theme(app: QApplication) -> None:
    """Apply a Fusion-based dark palette + bundled stylesheet."""
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(BG))
    pal.setColor(QPalette.WindowText, QColor(TEXT))
    pal.setColor(QPalette.Base, QColor("#0B0E13"))
    pal.setColor(QPalette.AlternateBase, QColor(PANEL))
    pal.setColor(QPalette.Text, QColor(TEXT))
    pal.setColor(QPalette.Button, QColor("#1E2430"))
    pal.setColor(QPalette.ButtonText, QColor(TEXT))
    pal.setColor(QPalette.Highlight, QColor(ACCENT))
    pal.setColor(QPalette.HighlightedText, QColor("#0A0E13"))
    pal.setColor(QPalette.ToolTipBase, QColor(PANEL))
    pal.setColor(QPalette.ToolTipText, QColor(TEXT))
    pal.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#5A6473"))
    pal.setColor(QPalette.Disabled, QPalette.Text, QColor("#5A6473"))
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#5A6473"))
    app.setPalette(pal)

    try:
        qss = (
            resources.files("image_editor.resources")
            .joinpath("styles.qss")
            .read_text(encoding="utf-8")
        )
        app.setStyleSheet(qss)
    except (FileNotFoundError, ModuleNotFoundError):
        pass
