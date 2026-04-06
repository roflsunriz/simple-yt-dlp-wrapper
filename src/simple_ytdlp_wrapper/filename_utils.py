from __future__ import annotations

import re


INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')
CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


def sanitize_file_basename(title: str, max_length: int = 32) -> str:
    text = CONTROL_CHARS.sub("", title or "")
    text = INVALID_CHARS.sub("_", text)
    text = text.strip().rstrip(".")
    if not text or text.isspace():
        text = "video"
    text = text[:max_length].rstrip(" .")
    if not text:
        text = "video"
    if text.upper() in WINDOWS_RESERVED:
        text = f"{text}_"
    return text
