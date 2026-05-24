from __future__ import annotations

import sys
from importlib import resources

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from image_editor.config import APP_ID, APP_NAME, APP_ORG
from image_editor.ui.main_window import MainWindow
from image_editor.ui.theme import apply_dark_theme
from image_editor.utils.logger import get_logger


def _resource_path(name: str) -> str | None:
    try:
        with resources.as_file(
            resources.files("image_editor.resources").joinpath(name)
        ) as p:
            return str(p) if p.is_file() else None
    except (FileNotFoundError, ModuleNotFoundError):
        return None


def _app_icon() -> QIcon:
    p = _resource_path("app.ico")
    return QIcon(p) if p else QIcon()


def _splash_pixmap() -> QPixmap | None:
    p = _resource_path("splash.png")
    if not p:
        return None
    pix = QPixmap(p)
    if pix.isNull():
        return None
    # Scale to a comfortable startup size.
    return pix.scaled(520, 520, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def main(argv: list[str] | None = None) -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName(APP_ORG)
    app.setApplicationVersion("1.0.0")
    app.setDesktopFileName(APP_ID)

    apply_dark_theme(app)

    icon = _app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    splash: QSplashScreen | None = None
    splash_pix = _splash_pixmap()
    if splash_pix is not None:
        splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        splash.setAttribute(Qt.WA_TranslucentBackground, True)
        splash.showMessage(
            "  Loading Vibrance…",
            Qt.AlignBottom | Qt.AlignLeft,
            Qt.white,
        )
        splash.show()
        app.processEvents()

    get_logger().info("starting %s", APP_NAME)
    window = MainWindow()
    if not icon.isNull():
        window.setWindowIcon(icon)

    def _show_main() -> None:
        window.show()
        if splash is not None:
            splash.finish(window)

    # Brief splash so users see the brand on launch, then the main window.
    if splash is not None:
        QTimer.singleShot(900, _show_main)
    else:
        _show_main()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
