"""Deprecated compatibility entry point; browser-cookie extraction is disabled."""

if __name__ == "__main__":
    raise SystemExit(
        "IAM no longer imports Firefox/browser cookies.\n"
        "Instead run: python -m iam --username YOUR_NAME login\n"
        "This uses instagrapi session settings with private file permissions."
    )
