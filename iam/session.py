"""Instagram session lifecycle. No browser-cookie harvesting, no plaintext passwords."""
from __future__ import annotations

import os
import secrets
import json
from pathlib import Path
from typing import Any, Callable
from .errors import IAMError
from .settings import app_home, private_dir, save_selected_user, session_path
from .validation import username


def default_client() -> Any:
    try:
        from instagrapi import Client
    except ImportError as exc:
        raise IAMError("instagrapi is missing. Run `python -m pip install -e .`.") from exc
    return Client()


class SessionManager:
    def __init__(self, *, home: Path | None = None, client_factory: Callable[[], Any] = default_client):
        self.home = home if home is not None else app_home()
        self.client_factory = client_factory

    def _safe_path(self, account: str) -> Path:
        root = private_dir(self.home)
        folder = private_dir(root / "sessions")
        target = session_path(account, self.home)
        if target.is_symlink():
            raise IAMError("Refusing symlinked session file.")
        return target

    def login(self, account: str, password: str, verification_code: str = "") -> Any:
        account = username(account)
        if not password:
            raise IAMError("A password is required for login.")
        target = self._safe_path(account)
        client = self.client_factory()
        if target.is_file():
            try:
                client.load_settings(str(target))
            except (ValueError, OSError, TypeError) as exc:
                raise IAMError("Saved session is corrupted. Run `iam logout --username NAME` before retrying.") from exc
        kwargs = {"verification_code": verification_code} if verification_code else {}
        if client.login(account, password, **kwargs) is False:
            raise IAMError("Authentication was rejected by Instagram.")
        self._save(client, target)
        save_selected_user(account, self.home)
        return client

    def _save(self, client: Any, target: Path) -> None:
        target = self._safe_path(target.stem)
        temp = target.parent / f".{target.stem}.{secrets.token_hex(8)}.tmp"
        try:
            # Restrictive permissions exist before instagrapi opens the file.
            fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(fd)
            client.dump_settings(str(temp))
            if os.name == "posix":
                temp.chmod(0o600)
            if not temp.is_file() or not temp.stat().st_size:
                raise IAMError("Instagram did not produce a valid session file.")
            try:
                if not isinstance(json.loads(temp.read_text(encoding="utf-8")), dict):
                    raise ValueError("Not an object")
            except (ValueError, UnicodeError) as exc:
                raise IAMError("Instagram returned invalid session settings.") from exc
            os.replace(temp, target)
            if os.name == "posix":
                target.chmod(0o600)
        finally:
            temp.unlink(missing_ok=True)

    def restore(self, account: str) -> Any:
        """Try saved session without a new login; verify it by calling account_info."""
        target = self._safe_path(account)
        if not target.is_file():
            raise IAMError("No saved session. Run `iam login --username NAME` first.")
        client = self.client_factory()
        client.load_settings(str(target))
        try:
            profile = client.account_info()
        except Exception as exc:
            raise IAMError("Session is not usable. Run `iam --username NAME login` again.") from exc
        actual = profile.get("username") if isinstance(profile, dict) else getattr(profile, "username", None)
        if not actual or username(actual) != username(account):
            raise IAMError("Saved session does not belong to the requested account.")
        return client

    def logout(self, account: str) -> None:
        self._safe_path(account).unlink(missing_ok=True)
        # Only local session deletion; server-side sessions can be revoked in Instagram.
