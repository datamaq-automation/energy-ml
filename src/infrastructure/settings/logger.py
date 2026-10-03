"""src/infrastructure/settings/logger.py — Logging con el mismo formato que uvicorn ("INFO:     mensaje")."""

from __future__ import annotations

import logging
import sys

from uvicorn.logging import DefaultFormatter

from src.infrastructure.settings.config import get_settings


def setup_logging() -> logging.Logger:
    settings = get_settings()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Mismo formateador que uvicorn: nivel alineado y con color si la salida es una terminal.
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(DefaultFormatter("%(levelprefix)s %(message)s", use_colors=None))

    logger = logging.getLogger(settings.PROJECT_NAME)
    logger.handlers = [handler]
    logger.setLevel(log_level)
    logger.propagate = False
    return logger


logger = setup_logging()
