#!/usr/bin/env python3
"""Desinstala Claude Session Guard. NO borra tus respaldos (~/claude-backups)."""
import os
import platform
import subprocess
from pathlib import Path

HOME = Path.home()


def rm(p):
    try:
        Path(p).unlink()
    except Exception:
        pass


def main():
    # detener watcher si corre
    try:
        import guard
        guard.stop_watcher()
    except Exception:
        pass

    s = platform.system()
    if s == "Linux":
        rm(HOME / ".config/autostart/claude-session-guard.desktop")
        rm(HOME / ".local/share/applications/claude-session-guard.desktop")
        rm(HOME / ".local/share/icons/claude-session-guard.svg")
    elif s == "Darwin":
        plist = HOME / "Library/LaunchAgents/com.claudesessionguard.watcher.plist"
        subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
        rm(plist)
    elif s == "Windows":
        appdata = Path(os.environ["APPDATA"])
        rm(appdata / "Microsoft/Windows/Start Menu/Programs/Startup/claude-session-guard.bat")
        rm(appdata / "Microsoft/Windows/Start Menu/Programs/Claude Session Guard.bat")

    print("Desinstalado. Tus respaldos en ~/claude-backups siguen intactos.")


if __name__ == "__main__":
    main()
