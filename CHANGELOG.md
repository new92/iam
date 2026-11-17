# Changelog

## 1.0.0 — 2026-11-17

- Reimplemented IAM as an import-safe, typed Python package with CLI and interactive shell.
- Fixed invalid JSON metadata; removed `sudo pip`, browser-cookie extraction, destructive recursive uninstall and auto-install-on-import behavior.
- Added secure per-account saved session permissions, confirmation prompts, dry run, bounded queries, and restricted exports.
- Restricted security information to non-sensitive status fields and suppressed unknown exception content that could contain secrets.
- Added targeted profile, social graph, media, collections, highlights, engagement, privacy and notification operations.
- Replaced IGTV publishing with an explicit Reel command; dropped bulk growth, mass engagement and anonymity claims.
- Added 68+ offline tests, CI matrix, CodeQL, Dependabot and improved security, migration and contributing documentation.

This is a **behavioral rewrite**, not a one-to-one preservation of the original 56 menu options. Instagram API compatibility remains unverified without live account testing.
