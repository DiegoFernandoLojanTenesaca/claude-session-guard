<h1 align="center">🛡 Claude Session Guard</h1>

<p align="center">Auto-backup &amp; watchdog for your <b>Claude Code</b> session — Linux · macOS · Windows.</p>

---

Every time you open Claude Code it rotates the OAuth token in
`~/.claude/.credentials.json`. If that file gets cleared or lost, you're
logged out — annoying on your main box, blocking on a fresh machine.

Claude Session Guard runs a tiny background watcher that:

- **snapshots** your credentials + config whenever the token changes, so you
  always keep the freshest *valid* token,
- **guards** the token — if it disappears or empties, it fires a notification
  (and can auto-restore the last good copy), and
- **keeps it alive** — the `refreshToken` only renews when Claude *starts*, so
  after a few idle days it can expire on its own. If you haven't refreshed in
  a while, Guard runs `claude -p` headless to renew it (which also doubles as a
  token health-check). No SDK, no API key — it drives the real CLI so it
  refreshes the actual OAuth session.

It never overwrites a good backup with a broken one — it validates
`claudeAiOauth.accessToken` before every snapshot.

Files backed up:

| File | What |
|------|------|
| `~/.claude/.credentials.json` | OAuth token (the important one) |
| `~/.claude/.last-cleanup` | cleanup marker |
| `~/.claude.json` | projects / MCP config |

Snapshots land in `~/claude-backups/YYYY-MM-DD_HHMMSS/` (last 50 kept, dir `700`, files `600`).

## Why not FileWatcher / inotify / a cron job?

Those detect "a file changed" — they don't know what a *broken token* is, so
they'd happily overwrite your good backup with an empty file. This validates
the token first and never clobbers a good copy with a bad one. Pure Python
stdlib, nothing to compile.

## Requirements

- **Python 3.8+** (already on macOS/most Linux; on Windows get it from python.org).
- **Tk** for the GUI — bundled with Python on Windows/macOS; on Linux install `python3-tk`.
- The **`claude` CLI** on your `PATH` — only needed for the keepalive feature.

That's it. No `pip install`.

## Install

```bash
git clone https://github.com/YOURNAME/claude-session-guard
cd claude-session-guard
python3 install.py        # Windows: py install.py
```

This registers the watcher to start on login (systemd-less: XDG autostart on
Linux, LaunchAgent on macOS, Startup folder on Windows), adds a launcher, and
starts watching now.

## Use

Open **Claude Session Guard** from your apps menu, or run the CLI:

```bash
python3 guard.py            # GUI
python3 guard.py backup     # snapshot now
python3 guard.py restore    # restore latest (e.g. on a new PC)
python3 guard.py keepalive  # renew + test the token now (runs `claude -p`)
python3 guard.py watch 60   # foreground watcher
```

**Move a session to a new machine:** copy `~/claude-backups/` over, run
`python3 guard.py restore`, restart Claude Code.

### Options (environment variables)

- `CLAUDE_BACKUP_DIR=/path` — back up to an external drive / synced folder.
- `RESTORE_ON_LOSS=1` — auto-restore the last good copy if the token vanishes
  (off by default; it can race a live write).
- `KEEP=50` — how many snapshots to keep.
- `REFRESH_EVERY=172800` — seconds of inactivity before a keepalive runs (2 days).
- `KEEPALIVE_MODEL=haiku` — model used for the keepalive ping (cheapest by default).
- `CLAUDE_BIN=/path/to/claude` — override the Claude CLI location for keepalive.

## Platform notes

- **Linux** — the tested platform. GUI uses XWayland under Wayland; no tray
  icon (GNOME dropped legacy trays), so it's a window + `.desktop` launcher.
- **Windows** — the watcher runs via a `pythonw` Startup entry (no console
  window). Token-loss notifications go to `~/claude-backups/guard.log`.
- **macOS** — ⚠️ Claude Code may store the OAuth token in the **login
  Keychain** instead of a file. When there's no `.credentials.json`, only
  `~/.claude.json` config is backed up; Keychain credentials are out of scope.

## Security

Backups contain your OAuth tokens (kept `700`/`600`). If you point
`CLAUDE_BACKUP_DIR` at a cloud-synced folder, your tokens go to that cloud —
your call.

## Uninstall

```bash
python3 uninstall.py   # keeps your backups
```

## License

MIT
