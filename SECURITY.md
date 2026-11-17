# Security policy

## Supported versions

Only the newest `1.x` release of the rewritten IAM CLI receives fixes. The historical `0.x` script remains unsupported.

## Reporting security issues

Please use **GitHub private vulnerability reporting** under the repository's Security tab, if enabled. Otherwise privately contact the maintainer by an established non-public channel. Do not publish passwords, access tokens, backup codes, TOTP seeds, cookies, session files or private user data in public issues or logs. Include a minimal reproducible case with redacted logs and impact assessment.

## Threat model and limitations

- The upstream Instagram wrapper is an unofficial private API client. Sessions can be invalidated, throttled or challenged.
- Authentication stores instagrapi session settings in files restricted to the local user (POSIX 0600; directories 0700). **These files are not encrypted** and can be read by a compromised machine or privileged user.
- IAM does not load Firefox/browser cookies or attempt to bypass challenges, 2FA or permissions.
- Normal account and security output is limited to explicit allowlists; do not change them to print complete client objects.
- Mutating actions ask for affirmative confirmation unless `--yes` is explicitly supplied. There is no batch mode.
- Do not share shell history, crash reports or exported JSON containing private account information.
- Run as an ordinary user in a virtual environment; do not use `sudo pip` or distribute session files.
- Secrets are never required in environment variables, CLI parameters or config.json.

To revoke sessions, use Instagram's login-activity controls; deleting IAM's local session file only removes the local copy.
