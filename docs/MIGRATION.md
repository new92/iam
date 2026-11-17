# Migration from original IAM.py

The original `IAM.py` contains approximately 3,300 lines of interactive procedural logic, with global lists, recursive menus, platform-specific privilege escalation, immediate external requests and widespread `except Exception`. This rewrite is **not a drop-in command-number replacement**. Its purpose is to keep useful personal account management tasks, make them easier to test, and improve security by removing unsafe defaults.

## What changed

| Legacy | New behavior |
|---|---|
| `python cookies.py` reads Firefox SQLite cookies | Disabled; `python -m iam --username NAME login` prompts securely |
| `python IAM.py` asks for menu number then login | `python IAM.py <command>` or `python -m iam <command>` |
| Repeated login per command | Per-account saved session settings with verification; optional interactive shell |
| Hidden mutable globals | `AccountManager` instance with explicit client and username |
| Credentials/session fields potentially displayed | Security-summary allowlist and redacted third-party errors |
| Default broad actions and mass engagement | Only one user-selected change at a time, with explicit confirmation |
| Missing Conda `environment.yml` in CI | Pip build/test matrix and CodeQL |
| Invalid `config.json` | Valid JSON metadata |
| Browser cookie imports | Avoided; insecure cookie migration is not performed |
| Uninstaller scanning `/` and deleting directories | Removed; delete extracted project and session directory manually |
| Claims of anonymous access to private stories | Removed; all access follows Instagram permissions |
| 999 for script info | `python -m iam --version` or `python -m iam doctor` |

## Known limitations

- No backward-compatible numbered-menu interface, automatic bulk engagement, scraping automation or action scheduler.
- Most live Instagram commands cannot be tested without an authorized account and may need updating if instagrapi changes.
- Saved session settings are private by filesystem permission but **not encrypted at rest**.
- Read-only follower comparisons use samples; they cannot establish a full set unless all results are explicitly fetched.
- The replacement archive is generated from a reviewed source snapshot and implemented afresh; it does not contain the original 131 KB `IAM.py` or original PNG screenshots.
- Features tied to discontinued Instagram capabilities (such as IGTV publishing) are not replicated.

## If you need an unsupported workflow

Prefer an official API or Instagram's own app where available. For new functionality, add an independently testable method to `iam/operations.py`, a single-action CLI entry in `iam/cli.py`, a regression test, and a documentation entry. Avoid global state, mass actions, and secret logging.
