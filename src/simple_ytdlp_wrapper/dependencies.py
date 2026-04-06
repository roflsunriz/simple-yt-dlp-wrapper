from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .config import APP_DIR


@dataclass
class DependencyStatus:
    yt_dlp_path: str | None
    ffmpeg_path: str | None

    @property
    def has_yt_dlp(self) -> bool:
        return bool(self.yt_dlp_path)

    @property
    def has_ffmpeg(self) -> bool:
        return bool(self.ffmpeg_path)


def _find_executable(name: str) -> str | None:
    for candidate in (APP_DIR / name, APP_DIR / f"{name}.exe"):
        if candidate.exists():
            return str(candidate)
    return shutil.which(name) or shutil.which(f"{name}.exe")


def detect_dependencies() -> DependencyStatus:
    return DependencyStatus(
        yt_dlp_path=_find_executable("yt-dlp"),
        ffmpeg_path=_find_executable("ffmpeg"),
    )
