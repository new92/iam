"""Argparse-based CLI with single-action confirmation and mockable dispatch."""
from __future__ import annotations

import argparse
from datetime import date, datetime
from enum import Enum
import getpass
import importlib.util
import json
import os
from pathlib import Path
import shlex
import sys
from typing import Any, Callable

from . import __version__
from .errors import IAMError, public_error
from .operations import AccountManager
from .session import SessionManager, default_client
from .settings import app_home, selected_user
from .validation import identifier, local_media, nonempty_text, username


READ_OPS = {
    "account", "security", "profile", "from-id", "followers", "following",
    "not-following-back", "pending", "blocked", "posts", "stories", "highlights",
    "saved", "tagged", "story-viewers", "media", "highlight", "collections", "liked",
}
WRITE_OPS = {
    "follow", "unfollow", "block", "unblock", "approve", "reject", "bio",
    "photo", "story", "avatar", "direct", "like", "unlike", "save", "unsave",
    "comment", "delete", "download-media", "download-story", "reel", "notification",
}
USER_TARGET = {"follow", "unfollow", "block", "unblock", "approve", "reject",
               "remove-follower", "close-friend-add", "close-friend-remove"}
MEDIA_TARGET = {"like", "unlike", "save", "unsave", "delete", "download-media", "download-story"}


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="iam", description="Secure, human-directed Instagram account management")
    parser.add_argument("--username", help="Your signed-in Instagram username")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON (safe, filtered fields only)")
    parser.add_argument("--output", help="Write filtered result to a new, private JSON file")
    parser.add_argument("--yes", action="store_true", help="Explicitly approve one account-changing action")
    parser.add_argument("--dry-run", action="store_true", help="Preview an account-changing action without connecting")
    parser.add_argument("--version", action="version", version=f"iam {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    login = sub.add_parser("login", help="Authenticate and securely save session settings")
    login.add_argument("--username", default=argparse.SUPPRESS)
    login.add_argument("--two-factor", action="store_true", help="Prompt for a verification code")
    logout = sub.add_parser("logout", help="Delete local saved session (does not revoke Instagram sessions)")
    logout.add_argument("--username", default=argparse.SUPPRESS)
    sub.add_parser("doctor", help="Check local installation without contacting Instagram")
    sub.add_parser("shell", help="Interactive command shell (one authentication per session)")

    for cmd in ("account", "security", "not-following-back", "pending", "blocked", "saved", "liked", "collections"):
        p = sub.add_parser(cmd)
        if cmd not in ("account", "security"):
            p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("profile"); p.add_argument("target", nargs="?")
    p = sub.add_parser("from-id"); p.add_argument("pk")
    for cmd in ("followers", "following", "posts", "stories", "highlights", "tagged"):
        p = sub.add_parser(cmd)
        p.add_argument("target", nargs="?", help="Another account; omit to inspect your own")
        p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("story-viewers"); p.add_argument("pk"); p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("media"); p.add_argument("pk")
    p = sub.add_parser("highlight"); p.add_argument("pk")
    for cmd in sorted(USER_TARGET):
        p = sub.add_parser(cmd)
        p.add_argument("target")
    p = sub.add_parser("notification"); p.add_argument("target"); p.add_argument("kind", choices=["posts", "reels", "stories", "videos"]); p.add_argument("state", choices=["on", "off"])
    p = sub.add_parser("bio"); p.add_argument("text")
    p = sub.add_parser("photo"); p.add_argument("path"); p.add_argument("--caption", default="")
    p = sub.add_parser("story"); p.add_argument("path")
    p = sub.add_parser("reel"); p.add_argument("path"); p.add_argument("--caption", default="")
    p = sub.add_parser("avatar"); p.add_argument("path")
    p = sub.add_parser("direct"); p.add_argument("target"); p.add_argument("message")
    for cmd in sorted(MEDIA_TARGET):
        p = sub.add_parser(cmd)
        p.add_argument("pk")
        if cmd.startswith("download"):
            p.add_argument("--folder", default="downloads")
    p = sub.add_parser("comment"); p.add_argument("pk"); p.add_argument("text")
    return parser


def sanitize_args(args: argparse.Namespace) -> dict[str, Any]:
    """Provide a brief preview without ever showing message bodies or passwords."""
    a = vars(args)
    result = {"action": args.command, "will_contact_instagram": True, "dry_run": bool(args.dry_run)}
    for key in ("target", "pk", "path", "folder"):
        if key in a and a[key] is not None:
            result[key] = a[key]
    if "text" in a or "message" in a:
        result["content"] = "[user-supplied text omitted]"
    return result


def validate_action(args: argparse.Namespace) -> None:
    command = args.command
    if command in USER_TARGET or command in {"direct", "notification"}:
        username(args.target)
    if command in MEDIA_TARGET or command in {"comment"}:
        identifier(args.pk)
    if command in {"photo", "story", "avatar", "reel"}:
        local_media(args.path, kind="video" if command == "reel" else "photo")
    if command == "bio":
        nonempty_text(args.text, max_length=150)
    if command == "direct":
        nonempty_text(args.message, max_length=1000)
    if command == "comment":
        nonempty_text(args.text)


def execute(args: argparse.Namespace, mgr: AccountManager) -> Any:
    c = args.command
    if c == "account": return mgr.account()
    if c == "security": return mgr.security()
    if c == "profile": return mgr.user(args.target) if args.target else mgr.account()
    if c == "from-id": return mgr.username_from_id(args.pk)
    if c == "followers": return mgr.followers(args.target, args.limit)
    if c == "following": return mgr.following(args.target, args.limit)
    if c == "not-following-back": return mgr.not_following_back(args.limit)
    if c == "pending": return mgr.pending(args.limit)
    if c == "blocked": return mgr.blocked(args.limit)
    if c == "posts": return mgr.posts(args.target, args.limit)
    if c == "stories": return mgr.stories(args.target, args.limit)
    if c == "highlights": return mgr.highlights(args.target, args.limit)
    if c == "saved": return mgr.saved(args.limit)
    if c == "liked": return mgr.liked(args.limit)
    if c == "collections": return mgr.collections(args.limit)
    if c == "tagged": return mgr.tagged(args.target, args.limit)
    if c == "story-viewers": return mgr.story_viewers(args.pk, args.limit)
    if c == "media": return mgr.media(args.pk)
    if c == "highlight": return mgr.highlight(args.pk)
    if c in USER_TARGET: return getattr(mgr, c.replace("-", "_"))(args.target)
    if c == "notification": return mgr.notification(args.target, args.kind, args.state)
    if c == "bio": return mgr.bio(args.text)
    if c == "photo": return mgr.photo(args.path, args.caption)
    if c == "story": return mgr.story(args.path)
    if c == "reel": return mgr.reel(args.path, args.caption)
    if c == "avatar": return mgr.avatar(args.path)
    if c == "direct": return mgr.direct(args.target, args.message)
    if c in {"like", "unlike", "save", "unsave", "delete"}: return getattr(mgr, c)(args.pk)
    if c == "comment": return mgr.comment(args.pk, args.text)
    if c == "download-media": return mgr.download_media(args.pk, args.folder)
    if c == "download-story": return mgr.download_story(args.pk, args.folder)
    raise IAMError(f"Unknown command: {c}")


def json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (date, datetime, Path, Enum)):
        return str(value.value if isinstance(value, Enum) else value)
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    # No generic object/pydantic model serialization: may contain credentials.
    return "[unsupported value]"


def private_output(data: Any, location: str) -> None:
    path = Path(location).expanduser()
    if path.exists() or path.is_symlink():
        raise IAMError("Output file already exists; choose a different filename.")
    if not path.parent.is_dir():
        raise IAMError("Output directory does not exist.")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(json_value(data), handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def doctor() -> dict[str, Any]:
    return {
        "iam": __version__, "python": sys.version.split()[0],
        "instagrapi_installed": importlib.util.find_spec("instagrapi") is not None,
        "config_directory": str(app_home()),
        "browser_cookie_import": "disabled",
        "mode": "manual, user-confirmed actions",
    }


def print_result(result: Any, *, json_mode: bool = False, output: str | None = None) -> None:
    if output:
        private_output(result, output)
        print(f"Wrote filtered JSON to {output}")
    else:
        # JSON is deterministic and friendly for automation; rich is optional.
        print(json.dumps(json_value(result), ensure_ascii=False, indent=2))


def _require_identity(args: argparse.Namespace, home: Path) -> str:
    chosen = args.username or selected_user(home)
    if not chosen:
        raise IAMError("No account selected. Run `iam --username YOUR_NAME login` first.")
    return username(chosen)


def _restore_or_login(session: SessionManager, account: str, secret_input: Callable[[str], str]) -> Any:
    try:
        return session.restore(account)
    except IAMError:
        if not sys.stdin.isatty():
            raise IAMError("No usable session. Run `iam --username NAME login` interactively first.")
        password = secret_input("Instagram password (never stored by IAM): ")
        return session.login(account, password)


def _confirm(args: argparse.Namespace, input_fn: Callable[[str], str]) -> bool:
    if args.yes:
        return True
    if not sys.stdin.isatty():
        raise IAMError("Writes require confirmation. In automation, pass --yes explicitly.")
    answer = input_fn(f"Perform one '{args.command}' action? Type YES to proceed: ")
    return answer == "YES"


def run_shell(parser: argparse.ArgumentParser, mgr: AccountManager, input_fn: Callable[[str], str]) -> None:
    print("IAM interactive shell. Enter help to list commands; exit to quit.")
    while True:
        try:
            line = input_fn("iam> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if line in {"exit", "quit"}:
            return
        if line in {"", "help"}:
            print("Examples: account | security | followers --limit 10 | posts | photo PATH | follow USER")
            print("Use '<command> --help' for all options. Write actions ask for confirmation.")
            continue
        try:
            argv = shlex.split(line)
            subargs = parser.parse_args(argv)
            if subargs.command in {"login", "logout", "doctor", "shell"}:
                print("Run this command outside of the interactive shell.")
                continue
            if subargs.command in WRITE_OPS:
                validate_action(subargs)
                if subargs.dry_run:
                    print_result(sanitize_args(subargs)); continue
                if not _confirm(subargs, input_fn):
                    print("Cancelled."); continue
            print_result(execute(subargs, mgr), json_mode=subargs.json, output=subargs.output)
        except (IAMError, ValueError) as exc:
            print(f"Error: {public_error(exc)}", file=sys.stderr)
        except SystemExit:
            pass
        except Exception as exc:
            print(f"Error: {public_error(exc)}", file=sys.stderr)


def main(
    argv: list[str] | None = None, *,
    input_fn: Callable[[str], str] = input,
    secret_input: Callable[[str], str] = getpass.getpass,
    client_factory: Callable[[], Any] = default_client,
    home: Path | None = None,
) -> int:
    parser = make_parser()
    try:
        args = parser.parse_args(argv)
        home = home if home is not None else app_home()
        sessions = SessionManager(home=home, client_factory=client_factory)
        if args.command == "doctor":
            print_result(doctor(), json_mode=args.json, output=args.output)
            return 0
        if args.command == "login":
            account = _require_identity(args, home)
            pw = secret_input("Instagram password (never stored by IAM): ")
            code = secret_input("Verification code: ") if args.two_factor else ""
            sessions.login(account, pw, verification_code=code)
            print(f"Logged in as @{account}; encrypted transport used by instagrapi. Local session is private, not encrypted at rest.")
            return 0
        if args.command == "logout":
            account = _require_identity(args, home)
            sessions.logout(account)
            print(f"Deleted local session for @{account}. Revoke remote sessions in Instagram settings if needed.")
            return 0
        if args.command in WRITE_OPS:
            validate_action(args)
            if args.dry_run:
                result = sanitize_args(args)
                result["will_contact_instagram"] = False
                print_result(result, json_mode=args.json, output=args.output)
                return 0
            if not _confirm(args, input_fn):
                print("Cancelled; no request sent.")
                return 0
        account = _require_identity(args, home)
        client = _restore_or_login(sessions, account, secret_input)
        manager = AccountManager(client, account)
        if args.command == "shell":
            run_shell(parser, manager, input_fn)
            return 0
        result = execute(args, manager)
        print_result(result, json_mode=args.json, output=args.output)
        return 0
    except (IAMError, ValueError, OSError) as exc:
        print(f"Error: {public_error(exc)}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Error: {public_error(exc)}", file=sys.stderr)
        return 1
