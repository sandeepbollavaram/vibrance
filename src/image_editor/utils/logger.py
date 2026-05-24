from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from image_editor.config import LOG_DIR_NAME, user_data_dir

_LOGGER_NAME = "image_editor"
_configured = False


def get_logger() -> logging.Logger:
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)
    if _configured:
        return logger

    log_dir = user_data_dir() / LOG_DIR_NAME
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "image_editor.log"

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_h = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    file_h.setFormatter(fmt)

    stream_h = logging.StreamHandler()
    stream_h.setFormatter(fmt)

    logger.setLevel(logging.INFO)
    logger.addHandler(file_h)
    logger.addHandler(stream_h)
    logger.propagate = False
    _configured = True
    return logger
