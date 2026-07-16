from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .config import WINDOWS_BIN_DIR


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
    for candidate in (WINDOWS_BIN_DIR / name, WINDOWS_BIN_DIR / f"{name}.exe"):
        if candidate.exists():
            return str(candidate)
    return shutil.which(name) or shutil.which(f"{name}.exe")


def _resolve_command_wrapper(path: str | None, executable_name: str) -> str | None:
    if not path:
        return None

    wrapper_path = Path(path)
    if wrapper_path.suffix.lower() not in {".cmd", ".bat"}:
        return path

    try:
        wrapper_text = wrapper_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    executable_pattern = re.compile(
        rf'(?:"(?P<quoted>[^"\r\n]*{re.escape(executable_name)}\.exe)"|'
        rf'(?P<plain>[^\s"\r\n]*{re.escape(executable_name)}\.exe))',
        re.IGNORECASE,
    )
    for match in executable_pattern.finditer(wrapper_text):
        raw_candidate = match.group("quoted") or match.group("plain")
        expanded = os.path.expandvars(raw_candidate).replace("%~dp0", f"{wrapper_path.parent}{os.sep}")
        candidate = Path(expanded)
        if not candidate.is_absolute():
            candidate = wrapper_path.parent / candidate
        if candidate.is_file():
            return str(candidate.resolve())
    return None


def detect_dependencies() -> DependencyStatus:
    return DependencyStatus(
        yt_dlp_path=_find_executable("yt-dlp"),
        ffmpeg_path=_resolve_command_wrapper(_find_executable("ffmpeg"), "ffmpeg"),
    )
