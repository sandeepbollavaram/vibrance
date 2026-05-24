"""Local SVG icon loader.

Every icon ships in ``src/image_editor/resources/icons/`` and is loaded via
``QIcon(path)`` so the renderer rasterizes the SVG at whatever pixel size
the widget asks for. We use one neutral stroke color (#C9D2E0) so icons look
clean both on inactive dark buttons and on accent-blue active buttons.
"""

from __future__ import annotations

from functools import cache
from importlib import resources

from PySide6.QtGui import QIcon


@cache
def icon(name: str) -> QIcon:
    """Return the ``QIcon`` for ``<name>.svg`` from the bundled icons folder.

    Falls back to a null QIcon if the file isn't found, so a missing icon
    never crashes the UI."""
    try:
        with resources.as_file(
            resources.files("image_editor.resources.icons").joinpath(f"{name}.svg")
        ) as p:
            if p.is_file():
                return QIcon(str(p))
    except (FileNotFoundError, ModuleNotFoundError):
        pass
    return QIcon()


def icon_path(name: str) -> str | None:
    """Absolute path to the SVG file, or None if missing."""
    try:
        with resources.as_file(
            resources.files("image_editor.resources.icons").joinpath(f"{name}.svg")
        ) as p:
            return str(p) if p.is_file() else None
    except (FileNotFoundError, ModuleNotFoundError):
        return None
