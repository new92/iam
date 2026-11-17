"""Application errors and deliberately redacted messages."""
from __future__ import annotations

import re


class IAMError(Exception):
    """An actionable error appropriate for display to the user."""


_SENSITIVE = (
    (r"(?i)(password|passwd|sessionid|authorization|access_token|csrftoken|token|cookie)\s*[=:]\s*[^\s,;]+", r"\1=[REDACTED]"),
    (r"(?i)(bearer\s+)[a-z0-9._~+/-]+", r"\1[REDACTED]"),
)


def public_error(exc: BaseException) -> str:
    """Avoid exposing private API responses, tokens, or account secrets."""
    cls = type(exc).__name__
    known = {
        "LoginRequired": "Session expired. Run `iam login` to authenticate again.",
        "BadPassword": "Login failed. Verify your credentials in the official Instagram app.",
        "ChallengeRequired": "Instagram requires account verification. Complete it in the official app.",
        "ChallengeSelfieCaptcha": "Instagram requires an interactive verification step.",
        "PleaseWaitFewMinutes": "Instagram is throttling requests. Stop and retry later.",
        "RateLimitError": "Instagram rate limit reached. Stop and retry later.",
        "FeedbackRequired": "Instagram refused this action. Do not repeat it automatically.",
        "TwoFactorRequired": "Two-factor verification is required. Use the official app if prompted.",
    }
    if cls in known:
        return known[cls]
    if isinstance(exc, IAMError):
        return str(exc)
    # Unknown third-party exceptions may contain request bodies, phone numbers,
    # cookies or session information. Intentionally do not display their text.
    return f"Instagram operation failed ({cls}). See --help or try again later."


def redact(text: str) -> str:
    for pattern, replacement in _SENSITIVE:
        text = re.sub(pattern, replacement, text)
    return text
