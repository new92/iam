# Command reference

**Authentication and local tools:** `login`, `logout`, `doctor`, `shell`, `--version`.

**Read-only:** `account`, `security`, `profile [USER]`, `from-id ID`, `followers [USER]`, `following [USER]`, `not-following-back`, `pending`, `blocked`, `posts [USER]`, `stories [USER]`, `highlights [USER]`, `highlight ID`, `collections`, `saved`, `liked`, `tagged [USER]`, `story-viewers ID`, `media ID`.

**Single-action writes:** `follow USER`, `unfollow USER`, `block USER`, `unblock USER`, `remove-follower USER`, `approve USER`, `reject USER`, `close-friend-add USER`, `close-friend-remove USER`, `notification USER {posts,reels,stories,videos} {on,off}`, `bio TEXT`, `photo FILE [--caption TEXT]`, `reel FILE [--caption TEXT]`, `story FILE`, `avatar FILE`, `direct USER MESSAGE`, `like ID`, `unlike ID`, `save ID`, `unsave ID`, `comment ID TEXT`, `delete ID`, `download-media ID [--folder DIR]`, `download-story ID [--folder DIR]`.

**Global options** (place before command): `--username NAME`, `--dry-run`, `--yes`, `--json`, `--output FILE`.

All read-only list operations have a bounded `--limit` option where appropriate (1–100). `--dry-run` applies to write operations and never connects. `--output` creates a **new** JSON file and will not overwrite existing data.

## Legacy feature mapping

| Original option(s) | New command / disposition |
|---|---|
| 1, 2, 3 | `account`, `security`, `profile` |
| 4, 5, 6 | `pending`, `followers`, `following` |
| 7, 39, 40 | `highlights`, `highlight` (metadata only) |
| 8 | Not anonymous; `stories USER` and authorized `download-story ID` |
| 9, 10 | `saved`, `posts`; user-selected `download-media ID` |
| 11, 13, 14, 15 | `photo`, `avatar`, `story`, `reel` (IGTV retired) |
| 12 | `notification USER KIND STATE` |
| 16–19 | `follow`, `unfollow`, `approve`, `reject` |
| 20–21 | Bulk-following removed |
| 22–25 | `direct USER MESSAGE`; file/photo/video DMs not implemented |
| 26–29 | Bulk liking removed; targeted `like ID` |
| 30–32 | Targeted `comment ID TEXT`; automatic replies removed |
| 33–35 | `block`, `unblock`, `blocked` |
| 36–38 | Highlight editing not implemented |
| 41–45 | `stories`, `story-viewers`, `highlight`; deletion and hashtag harvesting removed |
| 46–47 | `bio`; country edit not implemented |
| 48–49 | `profile USER`, `tagged USER` |
| 50–51 | Password reset through Instagram app only; other profile edits deferred |
| 52–54 | `like`, `unlike`, `save`, `unsave`, `delete` |
| 55 | Scheduled actions removed |
| 56 | Story hide not implemented; use Instagram's privacy controls |
| 999 | `--version`, `doctor` |

**Note:** This is an explicit capability matrix, not a claim that every old behavior has been reimplemented.
