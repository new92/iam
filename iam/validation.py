"""Strict validation of user-supplied inputs."""
from __future__ import annotations

import re
from pathlib import Path
from .errors import IAMError

USERNAME_RE = re.compile(r"^[a-zA-Z0-9._]{1,30}$")
SUPPORTED_PHOTOS = {".jpg", ".jpeg", ".png"}
SUPPORTED_VIDEOS = {".mp4", ".mov"}


def username(value: str) -> str:
    val = value.strip().lstrip("@").lower()
    if not USERNAME_RE.fullmatch(val) or val.startswith(".") or val.endswith(".") or ".." in val:
        raise IAMError("Invalid Instagram username (letters, digits, underscores and single dots; max 30 characters).")
    return val


def identifier(value: str) -> str:
    if not str(value).isdigit() or int(value) <= 0:
        raise IAMError("ID must be a positive integer.")
    return str(value)


def bounded_limit(value: int, *, maximum: int = 100) -> int:
    if isinstance(value, bool) or not 1 <= value <= maximum:
        raise IAMError(f"Limit must be between 1 and {maximum}.")
    return value


def nonempty_text(value: str, *, max_length: int = 2200) -> str:
    val = value.strip()
    if not val or len(val) > max_length:
        raise IAMError(f"Text must be 1–{max_length} characters.")
    return val


def local_media(value: str, *, kind: str = "photo") -> Path:
    path = Path(value).expanduser()
    if not path.is_file():
        raise IAMError("The selected media file does not exist.")
    if path.is_symlink():
        raise IAMError("Symbolic-link media paths are not supported.")
    allowed = SUPPORTED_PHOTOS if kind == "photo" else SUPPORTED_VIDEOS
    if path.suffix.lower() not in allowed:
        raise IAMError(f"Unsupported {kind} extension. Allowed: {', '.join(sorted(allowed))}.")
    if path.stat().st_size > 100 * 1024 * 1024:
        raise IAMError("Files above 100 MiB are not supported by this CLI.")
    return path.resolve()
