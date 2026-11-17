# IAM — Instagram Account Manager

**Version 1.0.0 · Modernized community rewrite of new92/iam**

A command-line tool for **human-directed management of your own Instagram account**.

This version replaces the original 3,300+ line monolithic script with a typed, testable Python package. Its focus is clear permissions, safer session handling, short single-action workflows, and responsible use of the underlying Instagram client.

> **Status:** Offline tests pass; **live Instagram endpoints have NOT been validated** in this environment. IAM uses [instagrapi](https://github.com/subzeroid/instagrapi), an **unofficial** API wrapper. Instagram can change its API, challenge logins, or restrict automated use at any time. Nothing here bypasses account privacy, platform permissions, challenges, rate limits, or detection. Review Instagram's terms before use. Use only accounts that you own or are authorized to administer.

---

## Table of Contents

- [Highlights](#highlights)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Linux](#linux)
  - [macOS](#macos)
  - [Windows](#windows)
- [First-Time Setup](#first-time-setup)
- [Authentication](#authentication)
- [Usage](#usage)
- [Common Commands](#common-commands)
- [Account Management](#account-management)
- [Content Management](#content-management)
- [Download and Export](#download-and-export)
- [Interactive Shell](#interactive-shell)
- [Dry Run](#dry-run)
- [Update IAM](#update-iam)
- [Run Tests](#run-tests)
- [Compatibility and Migration](#compatibility-and-migration)
- [FAQ and Troubleshooting](#faq-and-troubleshooting)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## Highlights

- Private per-account session files (POSIX permissions `0600`, directories `0700`); no browser-cookie extraction and no password persisted by IAM itself.
- No root privileges, no automatic dependency installation, no recursive uninstall or filesystem-wide scanning.
- Read-only account, security-summary, follower/following, pending requests, saved media, collection, highlight, story and media inspection.
- **One account-changing action per CLI invocation**, with explicit `YES` confirmation or the opt-in `--yes` flag.
- Bounded queries (default 20, maximum 100), no bulk follow/like/comment/message actions, and no anonymous access promises.
- PII-aware output allowlists: backup codes, TOTP seeds, cookies and session IDs are never printed by account/security commands.
- `--dry-run` avoids all network access, `--output` writes filtered JSON to a newly created private file, and `doctor` checks local installation without a login.
- A terminal shell for repeated actions without repeated initialization.
- Offline unit tests, Python packaging, GitHub Actions CI, CodeQL, Dependabot and security reporting guidance.

## Requirements

Before installing IAM, make sure you have:

- Python **3.10 or newer**.
- Git installed on your system.
- An Instagram account that you own or are authorized to administer.
- An active internet connection for authentication and live account operations.

Check your Python installation:
```bash
python --version
```

On Linux and macOS, you may need:
```bash
python3 --version
```

Check Git:
```bash
git --version
```

## Installation

The recommended installation method is to clone the repository and install IAM inside a Python virtual environment.

This avoids modifying your system Python installation and keeps IAM's dependencies isolated.

### Linux

**1. Clone the repository**
```bash
git clone https://github.com/new92/IAM.git
```

**2. Navigate to the project directory**
```bash
cd IAM
```

**3. Create a virtual environment**
```bash
python3 -m venv .venv
```

**4. Activate the virtual environment**
```bash
source .venv/bin/activate
```

**5. Upgrade pip**
```bash
python -m pip install --upgrade pip
```

**6. Install IAM**
```bash
python -m pip install -e .
```

For development and testing dependencies:
```bash
python -m pip install -e ".[dev]"
```

**7. Verify the installation**
```bash
python -m iam doctor
```

**8. Check available commands**
```bash
python -m iam --help
```

### macOS

**1. Clone the repository**
```bash
git clone https://github.com/new92/IAM.git
```

**2. Navigate to the project directory**
```bash
cd IAM
```

**3. Create a virtual environment**
```bash
python3 -m venv .venv
```

**4. Activate the virtual environment**
```bash
source .venv/bin/activate
```

**5. Upgrade pip**
```bash
python -m pip install --upgrade pip
```

**6. Install IAM**
```bash
python -m pip install -e .
```

For development and testing dependencies:
```bash
python -m pip install -e ".[dev]"
```

**7. Verify the installation**
```bash
python -m iam doctor
```

**8. Check available commands**
```bash
python -m iam --help
```

### Windows

The following instructions use PowerShell.

**1. Clone the repository**
```powershell
git clone https://github.com/new92/IAM.git
```

**2. Navigate to the project directory**
```powershell
cd IAM
```

**3. Create a virtual environment**
```powershell
py -3 -m venv .venv
```

**4. Activate the virtual environment**
```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell prevents activation because of its execution policy, you can activate the environment using:
```powershell
.venv\Scripts\activate.bat
```

Alternatively, use Command Prompt instead of PowerShell.

**5. Upgrade pip**
```powershell
python -m pip install --upgrade pip
```

**6. Install IAM**
```powershell
python -m pip install -e .
```

For development and testing dependencies:
```powershell
python -m pip install -e ".[dev]"
```

**7. Verify the installation**
```powershell
python -m iam doctor
```

**8. Check available commands**
```powershell
python -m iam --help
```

> **Important:** Always activate your virtual environment before running IAM. You do not need administrator privileges, `sudo`, global Python package installation, or browser-cookie extraction.

## First-Time Setup

After installing IAM, verify that everything is working correctly.

Run:
```bash
python -m iam doctor
```

This checks the local installation without requiring an Instagram login.

To see all available commands:
```bash
python -m iam --help
```

You can also inspect the available options for a specific command:
```bash
python -m iam followers --help
```

## Authentication

IAM uses an authenticated Instagram session to access account information and perform authorized actions.

To log in:
```bash
python -m iam --username YOUR_USERNAME login
```

IAM will prompt you for your password interactively.

**Do not paste your password into commands or save it in shell history.**

If Instagram requires two-factor authentication, try:
```bash
python -m iam --username YOUR_USERNAME login --two-factor
```

Depending on Instagram's authentication flow, additional verification may be required.

### Session Storage

On successful authentication, IAM saves session settings under:
```text
~/.config/iam/sessions/YOUR_USERNAME.json
```

On Windows:
```text
%USERPROFILE%\.config\iam\sessions\
```

You can configure a different storage location using the `IAM_HOME` environment variable.

**Security warning:** Session files contain sensitive bearer/session material and are not encrypted at rest.

- Never commit session files to Git.
- Never upload them to public repositories.
- Never share them with other people.
- Avoid storing them in untrusted or publicly synchronized directories.
- Protect your computer and user account.

Passwords are prompted interactively and are not persisted by IAM itself.

Instagram may require you to authenticate again if a session expires or additional verification is requested.

## Usage

IAM uses a command-line interface rather than the original numbered interactive menu.

The general syntax is:
```bash
python -m iam [GLOBAL_OPTIONS] COMMAND [ARGUMENTS]
```

Global options must appear before the command name.

For example:
```bash
python -m iam --username YOUR_USERNAME followers --limit 20
```

Use:
```bash
python -m iam --help
```

to display the complete list of supported commands.

## Common Commands

### Account Information
```bash
# Display account information
python -m iam account

# Display a security summary
python -m iam security

# Display a user's profile information
python -m iam profile example_username

# Display followers
python -m iam followers --limit 20

# Display following
python -m iam following --limit 20

# Find accounts that do not follow you back
python -m iam not-following-back --limit 50

# Display pending follow requests
python -m iam pending-requests
```

**Note:** Only a security summary is displayed. Sensitive information such as backup codes, TOTP seeds, cookies and session identifiers is never printed.

The `not-following-back` command compares limited samples and may be incomplete. It does not claim to identify every nonreciprocal relationship.

### Media and Content Inspection
```bash
# Display recent posts
python -m iam posts --limit 10

# Display stories
python -m iam stories

# Display highlights
python -m iam highlights

# Display collections
python -m iam collections

# Display saved media
python -m iam saved

# Display story viewers
python -m iam story-viewers 123456789
```

These commands operate within the access permissions of your authenticated account.

## Account Management

IAM supports individual account-changing actions with explicit confirmation.

Examples:
```bash
# Follow a user
python -m iam follow example_username

# Unfollow a user
python -m iam unfollow example_username

# Block a user
python -m iam block example_username

# Remove a follower
python -m iam remove-follower example_username

# Change your biography
python -m iam bio "My new biography"

# Enable or disable notifications for a user
python -m iam notification example_username posts on
```

Each account-changing operation requires confirmation unless you explicitly use the `--yes` option.

For example:
```bash
python -m iam --yes follow example_username
```

Use `--yes` only when you have already reviewed and approved the exact action.

### Direct Messages
```bash
python -m iam direct friend_username "Hello!"
```

Messages should be sent only to people you are authorized to contact. IAM does not provide unsolicited bulk messaging workflows.

## Content Management

IAM supports individual media operations.

### Upload Media
```bash
# Upload a photo
python -m iam photo /path/to/photo.jpg --caption "A new post"

# Upload a reel
python -m iam reel /path/to/reel.mp4 --caption "A new reel"

# Upload a story
python -m iam story /path/to/story.jpg
```

### Interact with Media
```bash
# Like a post
python -m iam like 1234567890

# Comment on a post
python -m iam comment 1234567890 "Nice post!"

# Delete your own media
python -m iam delete 1234567890
```

The delete command checks that the media belongs to the currently authenticated account.

All account-changing operations require confirmation.

## Download and Export

IAM provides commands to download media that your authenticated account is permitted to access.

### Download Media
```bash
# Download media
python -m iam download-media 123456789 --folder ./downloads

# Download a story
python -m iam download-story 123456789 --folder ./downloads
```

You cannot use IAM to bypass private-account restrictions or access content that your account is not authorized to view.

### Export Account Information

You can export filtered account information to JSON:
```bash
python -m iam --output ./my-followers.json followers --limit 20
```

The output is written to a newly created private file.

Reports are not encrypted. Be careful when copying them, sharing them or storing them in cloud-synchronized directories.

## Interactive Shell

IAM also provides a terminal shell for users who want to execute multiple commands without repeatedly initializing the application.

Start the shell:
```bash
python -m iam shell
```

The shell is intended for interactive, human-directed use.

It does not introduce automated scheduling, bulk engagement or unattended action loops.

## Dry Run

Use `--dry-run` to inspect an operation without performing network activity.

Example:
```bash
python -m iam --dry-run follow example_username
```

Dry-run mode avoids all network access.

It is useful for checking the command structure before performing an account-changing action.

## Update IAM

To update an existing installation, navigate to the repository directory:
```bash
cd IAM
```

Pull the latest changes:
```bash
git pull
```

Activate your virtual environment if it is not already active.

Linux/macOS:
```bash
source .venv/bin/activate
```

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

Reinstall the updated package:
```bash
python -m pip install -e .
```

If you use the development dependencies:
```bash
python -m pip install -e ".[dev]"
```

Finally, verify the installation:
```bash
python -m iam doctor
```

> **Important:** Review the changelog and migration notes before updating. Back up important local data securely, and never upload or commit your session files.

## Run Tests

To install development dependencies:
```bash
python -m pip install -e ".[dev]"
```

Run the test suite:
```bash
python -m pytest -q
```

Run Ruff:
```bash
ruff check iam tests IAM.py cookies.py
```

Run Python compilation checks:
```bash
python -m compileall -q iam IAM.py cookies.py
```

All automated tests use a fake client. They do not log in or contact Instagram.

Live integration behavior must be verified manually with an explicitly authorized test account.

Avoid running destructive commands against your primary account during testing.

## Compatibility and Migration

IAM is a modernized rewrite of the original [new92/IAM](https://github.com/new92/IAM) project.

The original version used a numbered menu with 56 claimed actions. The modernized version replaces that interface with a structured command-line package.

### What Changed?

- `python IAM.py` still works as an entry point.
- `config.json` is valid JSON.
- `cookies.py` now explains the safer login process instead of reading Firefox's cookie database.
- Account-changing operations require explicit confirmation.
- Session handling uses private per-account session files.
- Commands have bounded query limits.
- Sensitive account information is filtered from output.

### Legacy Features

The original implementation included numerous workflows, such as:

- Account and security information.
- Followers and following inspection.
- Media downloads and uploads.
- Follow and unfollow operations.
- Direct messages.
- Likes and comments.
- Highlights and stories.
- Profile modifications.
- Scheduled actions.
- Anonymous story viewing.
- Bulk engagement operations.

**The modernized version does not retain all 56 original actions one-for-one.**

Unsupported or high-risk workflows are intentionally removed, including:

- Bulk following and unfollowing.
- Automated bulk liking and commenting.
- Unsolicited bulk direct messages.
- Anonymous private-story viewing promises.
- Password resets through the wrapper.
- Arbitrary scheduled actions.
- Automated target-list ingestion and engagement loops.

For exact feature coverage, consult:

- [MIGRATION.md](MIGRATION.md)
- [COMMANDS.md](COMMANDS.md)

The original repository's screenshots are not required for the modern CLI and are not included in this rewritten source package.

For historical implementation details, consult the upstream Git history.

## FAQ and Troubleshooting

### 1. How do I log in successfully?

Run:
```bash
python -m iam --username YOUR_USERNAME login
```

Enter your password when prompted.

If Instagram requests two-factor authentication, follow the verification instructions and try:
```bash
python -m iam --username YOUR_USERNAME login --two-factor
```

Instagram may also require additional verification.

### 2. Why does my session expire?

Instagram may invalidate sessions or request additional authentication.

If your session expires, authenticate again using the login command.

Never share your session file with anyone.

### 3. Why am I receiving a login challenge?

Instagram may request additional verification because of its authentication or security systems.

Complete the verification through Instagram's official channels.

IAM does not bypass authentication challenges.

### 4. Why is a command not working?

First, verify your installation:
```bash
python -m iam doctor
```

Then check the command's supported arguments:
```bash
python -m iam COMMAND --help
```

Make sure your virtual environment is active and that you are using the correct Python installation.

### 5. Where can I report a bug?

You can report issues through the repository's GitHub Issues page:

[Open a GitHub Issue](https://github.com/new92/IAM/issues)

When reporting a bug, include:

- Your operating system.
- Your Python version.
- The IAM command you executed.
- The error message or traceback.
- Steps to reproduce the issue.

**Never include passwords, session files, cookies, authentication tokens, backup codes or other sensitive information in bug reports.**

### 6. Can I use IAM with multiple accounts?

IAM supports per-account session storage.

Use the appropriate username when authenticating and running commands.

### 7. Does IAM guarantee that Instagram will not restrict my account?

No.

IAM uses an unofficial Instagram API wrapper. Instagram can change its API, restrict automated access, invalidate sessions or request additional verification.

Use the software responsibly and review Instagram's terms before use.

## Security

Security is a core part of the modernized IAM architecture.

The project follows these principles:

- No browser-cookie extraction.
- No password persistence by IAM itself.
- Private local session storage.
- Restrictive POSIX file permissions.
- No unnecessary root privileges.
- No automatic dependency installation.
- No recursive uninstall or filesystem-wide scanning.
- Filtered account and security output.
- Explicit confirmation for account-changing operations.
- Bounded data retrieval.
- Offline tests using a fake client.

Session files and exported reports may contain sensitive information. Protect them accordingly.

For additional information, see:

- [SECURITY.md](SECURITY.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## Contributing

Contributions are welcome!

Before submitting a pull request:

1. Read the contribution guidelines.
2. Review the project's code of conduct.
3. Make sure your changes follow the project's security principles.
4. Run the automated tests.
5. Include appropriate tests for new functionality.

Useful commands:
```bash
python -m pytest -q
ruff check iam tests IAM.py cookies.py
python -m compileall -q iam IAM.py cookies.py
```

Please avoid introducing automated bulk-engagement workflows, credential extraction or features that bypass Instagram's access restrictions.

See [CONTRIBUTING.md](CONTRIBUTING.md) for more information.

## Feedback

For bugs, suggestions and feature requests, please use the [repository's GitHub Issues page](https://github.com/new92/IAM/issues).

Please provide detailed information so that issues can be investigated and reproduced.

## License

This project is distributed under the MIT License.