"""Backward-compatible launcher: `python IAM.py`."""
from iam.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
