from __future__ import annotations

import re


INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')
CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
TRAILING_EXTENSION = re.compile(r"\.(mp4|mkv|webm|m4a|mp3|wav|aac|flac|mov|avi)$", re.IGNORECASE)
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


def sanitize_file_basename(value: str) -> str:
    text = CONTROL_CHARS.sub("", value or "")
    text = TRAILING_EXTENSION.sub("", text.strip())
    text = INVALID_CHARS.sub("_", text)
    text = text.strip().rstrip(".")
    if not text or text.isspace():
        text = "video"
    if text.upper() in WINDOWS_RESERVED:
        text = f"{text}_"
    return text


def suggest_file_basename(title: str, max_length: int = 32) -> str:
    text = sanitize_file_basename(title)[:max_length].rstrip(" .")
    return text or "video"
