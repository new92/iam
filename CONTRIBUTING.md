# Contributing

Contributions are welcome. Please submit small, testable changes and file a GitHub issue for substantial design changes.

1. Use Python 3.10+ and a virtual environment. Run `python -m pip install -e '.[dev]'`.
2. Add code to `iam/` (not the legacy compatibility launchers). Keep platform integration inside `iam/operations.py` and CLI parsing inside `iam/cli.py`.
3. Add offline tests with a fake client. Never check in real Instagram credentials, session files, captured HTTP responses, contact lists or other people's content.
4. Run `python -m pytest -q`, `ruff check iam tests IAM.py cookies.py`, and `python -m compileall -q iam IAM.py cookies.py`.
5. Keep operations bounded and human-directed. New mutation endpoints must have a clear confirmation path and a dry-run option. Use safe serializers and error handling; do not introduce bulk engagement or privacy bypasses.
6. Update `README.md`, `docs/COMMANDS.md` and `CHANGELOG.md` for user-facing changes.

For security flaws, use private reporting as described in `SECURITY.md`.
