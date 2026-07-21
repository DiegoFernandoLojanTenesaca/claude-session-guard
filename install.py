#!/usr/bin/env python3
"""Instalador de Claude Session Guard (Linux/macOS/Windows). Sin sudo.
Registra el watcher en el autostart del SO, crea un lanzador y arranca la vigilancia.
Corre en el sitio: no copia guard.py, apunta a esta carpeta. Si mueves la carpeta, reinstala.
"""
import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUARD = HERE / "guard.py"
ICON = HERE / "assets" / "logo.svg"
PY = sys.executable
HOME = Path.home()


def linux():
    apps = HOME / ".local/share/applications"
    icons = HOME / ".local/share/icons"
    autostart = HOME / ".config/autostart"
    bindir = HOME / ".local/bin"
    for d in (apps, icons, autostart, bindir):
        d.mkdir(parents=True, exist_ok=True)
    icon = icons / "claude-session-guard.svg"
    shutil.copy2(ICON, icon)
    # wrapper en el PATH: da el comando `claude-guard` y desacopla el .desktop del python.
    # Además recupera el entorno gráfico: en Wayland el menú a veces NO pasa XAUTHORITY,
    # y Tk (X/XWayland) no puede conectar al display -> la GUI "no abre" al hacer clic.
    launcher = bindir / "claude-guard"
    launcher.write_text(
        "#!/usr/bin/env bash\n"
        'for v in DISPLAY WAYLAND_DISPLAY XAUTHORITY; do\n'
        '  if [ -z "${!v}" ]; then\n'
        '    val=$(systemctl --user show-environment 2>/dev/null | sed -n "s/^$v=//p")\n'
        '    [ -n "$val" ] && export "$v=$val"\n'
        '  fi\n'
        'done\n'
        'if [ -z "$XAUTHORITY" ]; then\n'
        '  xa=$(ls -t "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"/.mutter-Xwaylandauth.* 2>/dev/null | head -1)\n'
        '  [ -n "$xa" ] && export XAUTHORITY="$xa"\n'
        'fi\n'
        '[ -z "$DISPLAY" ] && export DISPLAY=:0\n'
        f'exec "{PY}" "{GUARD}" "$@"\n')
    launcher.chmod(0o755)
    (apps / "claude-session-guard.desktop").write_text(
        "[Desktop Entry]\nType=Application\nName=Claude Session Guard\n"
        "Comment=Respalda y vigila tu sesión de Claude Code\n"
        f"Exec={launcher} %u\nTryExec={launcher}\nIcon={icon}\n"
        "Terminal=false\nStartupNotify=false\nStartupWMClass=claude-session-guard\n"
        "Keywords=claude;token;backup;session;respaldo;\nCategories=Utility;\n")
    (autostart / "claude-session-guard.desktop").write_text(
        "[Desktop Entry]\nType=Application\nName=Claude Session Guard Watcher\n"
        f"Exec={PY} {GUARD} watch\nTerminal=false\nStartupNotify=false\n"
        "X-GNOME-Autostart-enabled=true\n")
    subprocess.run(["update-desktop-database", str(apps)], capture_output=True)


def macos():
    la = HOME / "Library/LaunchAgents"
    la.mkdir(parents=True, exist_ok=True)
    plist = la / "com.claudesessionguard.watcher.plist"
    plist.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0"><dict>\n'
        '  <key>Label</key><string>com.claudesessionguard.watcher</string>\n'
        '  <key>ProgramArguments</key><array>'
        f'<string>{PY}</string><string>{GUARD}</string><string>watch</string></array>\n'
        '  <key>RunAtLoad</key><true/>\n  <key>KeepAlive</key><true/>\n'
        '</dict></plist>\n')
    subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
    subprocess.run(["launchctl", "load", str(plist)])


def windows():
    appdata = Path(os.environ["APPDATA"])
    startup = appdata / "Microsoft/Windows/Start Menu/Programs/Startup"
    programs = appdata / "Microsoft/Windows/Start Menu/Programs"
    for d in (startup, programs):
        d.mkdir(parents=True, exist_ok=True)
    pyw = Path(PY).with_name("pythonw.exe")
    exe = pyw if pyw.exists() else Path(PY)
    (startup / "claude-session-guard.bat").write_text(f'start "" "{exe}" "{GUARD}" watch\r\n')
    (programs / "Claude Session Guard.bat").write_text(f'start "" "{exe}" "{GUARD}"\r\n')


def start_watcher_now():
    if os.name == "nt":
        flags = dict(creationflags=0x00000008 | 0x08000000)
    else:
        flags = dict(start_new_session=True)
    subprocess.Popen([PY, str(GUARD), "watch"], **flags)


def main():
    s = platform.system()
    if s == "Linux":
        linux(); start_watcher_now()
    elif s == "Darwin":
        macos()  # launchctl load ya arranca el watcher
    elif s == "Windows":
        windows(); start_watcher_now()
    else:
        print("SO no soportado:", s); sys.exit(1)
    print(f"Instalado para {s}. Abre 'Claude Session Guard' o corre:  {PY} {GUARD}")


if __name__ == "__main__":
    main()
