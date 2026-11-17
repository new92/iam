"""Local application paths and non-secret preferences."""
from __future__ import annotations

import json
import os
from pathlib import Path
from .errors import IAMError
from .validation import username


def app_home() -> Path:
    override = os.environ.get("IAM_HOME")
    return Path(override).expanduser() if override else Path.home() / ".config" / "iam"


def private_dir(folder: Path) -> Path:
    if folder.exists() and folder.is_symlink():
        raise IAMError("Refusing to use a symlink as the IAM configuration directory.")
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix":
        if folder.stat().st_uid != os.getuid():
            raise IAMError("IAM configuration directory must be owned by the current user.")
        folder.chmod(0o700)
    return folder


def session_path(user: str, home: Path | None = None) -> Path:
    return (home if home is not None else app_home()) / "sessions" / (username(user) + ".json")


def save_selected_user(user: str, home: Path | None = None) -> None:
    folder = private_dir(home if home is not None else app_home())
    target = folder / "preferences.json"
    if target.is_symlink():
        raise IAMError("Refusing to overwrite symlinked preferences.")
    temp = folder / ".preferences.tmp"
    if temp.exists() and temp.is_symlink():
        raise IAMError("Refusing symlinked temporary preferences.")
    descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump({"selected_username": username(user)}, handle)
    os.replace(temp, target)
    if os.name == "posix":
        target.chmod(0o600)


def selected_user(home: Path | None = None) -> str | None:
    file = (home if home is not None else app_home()) / "preferences.json"
    if not file.exists():
        return None
    if file.is_symlink():
        raise IAMError("Refusing symlinked preferences.")
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
        return username(data["selected_username"])
    except (KeyError, json.JSONDecodeError, TypeError) as exc:
        raise IAMError("Preferences are invalid. Run `iam login --username YOUR_NAME`.") from exc
