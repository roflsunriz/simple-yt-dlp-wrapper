from __future__ import annotations

import logging
from datetime import datetime

from .config import LOG_DIR


def configure_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("simple_ytdlp_wrapper")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_DIR / f"{datetime.now():%Y-%m-%d}.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    *,
    url: str = "",
    code: str = "",
    detail: str = "",
) -> None:
    parts = [f"event={event}"]
    if url:
        parts.append(f"url={url}")
    if code:
        parts.append(f"code={code}")
    if detail:
        normalized = " ".join(str(detail).splitlines()).strip()
        parts.append(f"detail={normalized}")
    logger.log(level, " ".join(parts))
