#!/usr/bin/env python3
"""Claude Session Guard — backup + watchdog for the Claude Code session.

Cross-platform (Linux/macOS/Windows). No deps beyond the stdlib.
  guard.py              -> abre la GUI (por defecto)
  guard.py backup       -> snapshot ahora
  guard.py restore [dir]-> restaura el más reciente (o 'dir')
  guard.py watch [seg]   -> vigila el token (singleton via PID-file, def 60s)
  guard.py check        -> una pasada de watch
Env: CLAUDE_BACKUP_DIR (destino), KEEP (copias, def 50), RESTORE_ON_LOSS=1.
"""
import os
import sys
import json
import time
import shutil
import signal
import hashlib
import platform
import subprocess
from pathlib import Path
from datetime import datetime

HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
FILES = [CLAUDE_DIR / ".credentials.json", CLAUDE_DIR / ".last-cleanup", HOME / ".claude.json"]
CRED = CLAUDE_DIR / ".credentials.json"
DEST = Path(os.environ.get("CLAUDE_BACKUP_DIR", HOME / "claude-backups"))
KEEP = int(os.environ.get("KEEP", "50"))
RESTORE_ON_LOSS = os.environ.get("RESTORE_ON_LOSS", "0") == "1"
# El refreshToken solo se renueva al arrancar Claude; si no lo abres varios días
# caduca solo. keepalive corre `claude -p` para renovarlo (y de paso testear el token).
REFRESH_EVERY = int(os.environ.get("REFRESH_EVERY", str(2 * 24 * 3600)))  # cada 2 días
KEEPALIVE_MODEL = os.environ.get("KEEPALIVE_MODEL", "haiku")
CLAUDE_BIN = os.environ.get("CLAUDE_BIN") or shutil.which("claude") or str(HOME / ".local/bin/claude")
PIDFILE = DEST / ".watch.pid"
HASHFILE = DEST / ".last-hash"
REFRESHFILE = DEST / ".last-refresh"


# ---------- helpers ----------
def _stamp():
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")

def _log(msg):
    try:
        DEST.mkdir(parents=True, exist_ok=True)
        with (DEST / "guard.log").open("a") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}\n")
    except Exception:
        pass

def _lockdown(p):
    # 700 dirs / 600 files en POSIX; no-op en Windows
    try:
        if os.name == "posix":
            os.chmod(p, 0o700 if Path(p).is_dir() else 0o600)
    except Exception:
        pass

def notify(msg):
    s = platform.system()
    try:
        if s == "Linux":
            subprocess.run(["notify-send", "Claude Session Guard", msg], check=False)
        elif s == "Darwin":
            subprocess.run(["osascript", "-e",
                            f'display notification "{msg}" with title "Claude Session Guard"'], check=False)
        else:  # Windows u otros: sin toast garantizado, queda en el log
            print("AVISO:", msg)
    except Exception:
        print("AVISO:", msg)
    _log(msg)

def token_ok():
    """¿Existe el accessToken de la sesión de Claude (no los de MCP)?"""
    try:
        d = json.loads(CRED.read_text(encoding="utf-8"))
        return bool(d.get("claudeAiOauth", {}).get("accessToken"))
    except Exception:
        return False

def backups():
    return sorted(p for p in DEST.iterdir() if p.is_dir()) if DEST.exists() else []

def _last_refresh():
    try:
        return float(REFRESHFILE.read_text().strip())
    except Exception:
        return 0.0

def _touch_refresh():
    try:
        DEST.mkdir(parents=True, exist_ok=True)
        REFRESHFILE.write_text(str(time.time()))
    except Exception:
        pass

def keepalive():
    """Arranca Claude headless para renovar el token; sirve también de health-check.
    Devuelve (ok, detalle)."""
    exe = CLAUDE_BIN if Path(CLAUDE_BIN).exists() else shutil.which("claude")
    if not exe:
        return False, "no encuentro el binario 'claude' (define CLAUDE_BIN)"
    try:
        r = subprocess.run([exe, "-p", "responde solo: ok", "--model", KEEPALIVE_MODEL],
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            return True, "token vivo y renovado"
        return False, (r.stderr.strip()[:200] or f"claude salió con código {r.returncode}")
    except Exception as e:
        return False, str(e)[:200]


# ---------- comandos ----------
def backup():
    stamp = _stamp()
    d = DEST / stamp
    d.mkdir(parents=True, exist_ok=True)
    _lockdown(DEST); _lockdown(d)
    saved = 0
    for f in FILES:
        if f.exists():
            dst = d / f"{stamp}_{f.name}"
            shutil.copy2(f, dst); _lockdown(dst); saved += 1
    # purga a las últimas KEEP copias
    for old in backups()[:-KEEP]:
        shutil.rmtree(old, ignore_errors=True)
    return f"Respaldo en: {d.name}  ({saved} archivos)"

def restore(src=None):
    d = Path(src) if src else (backups()[-1] if backups() else None)
    if not d or not d.is_dir():
        raise RuntimeError(f"no hay respaldos en {DEST}")
    done = []
    for f in FILES:
        matches = sorted(d.glob(f"*{f.name}"))
        if matches:
            f.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(matches[0], f); done.append(f.name)
    if not done:
        raise RuntimeError(f"la carpeta {d.name} no tiene copias reconocibles")
    return f"Restaurado desde {d.name}: {', '.join(done)}. Reinicia Claude Code."

def check():
    if token_ok():
        h = hashlib.sha256(CRED.read_bytes()).hexdigest()
        last = HASHFILE.read_text().strip() if HASHFILE.exists() else ""
        if h != last:
            _log(backup())
            DEST.mkdir(parents=True, exist_ok=True)
            HASHFILE.write_text(h)
            _touch_refresh()   # el token acaba de renovarse por uso real
    else:
        notify("⚠️ token de Claude vacío/borrado en .credentials.json")
        if RESTORE_ON_LOSS:
            try:
                notify(restore())
            except Exception as e:
                _log(f"auto-restore falló: {e}")

def watch(interval=60):
    if watcher_pid():
        print("ya hay un watcher corriendo"); return
    DEST.mkdir(parents=True, exist_ok=True)
    PIDFILE.write_text(str(os.getpid()))
    signal.signal(signal.SIGTERM, lambda *_: (_cleanpid(), sys.exit(0)))
    print(f"Vigilando {CRED} cada {interval}s. Destino: {DEST}")
    try:
        while True:
            try:
                check()
            except Exception as e:
                _log(f"error en check: {e}")
            # keepalive solo si llevas REFRESH_EVERY sin renovar (idle real)
            try:
                if time.time() - _last_refresh() >= REFRESH_EVERY:
                    ok, detail = keepalive()
                    _log(f"keepalive: {'ok' if ok else 'FALLO'} — {detail}")
                    if ok:
                        _touch_refresh()
                    elif not token_ok():
                        notify("⚠️ keepalive falló y el token no está sano")
            except Exception as e:
                _log(f"error en keepalive: {e}")
            time.sleep(interval)
    finally:
        _cleanpid()

def _cleanpid():
    try:
        PIDFILE.unlink()
    except Exception:
        pass


# ---------- estado del watcher (cross-platform) ----------
def _alive(pid):
    try:
        if os.name == "posix":
            os.kill(pid, 0); return True
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                             capture_output=True, text=True).stdout
        return str(pid) in out
    except Exception:
        return False

def watcher_pid():
    try:
        pid = int(PIDFILE.read_text().strip())
        return pid if _alive(pid) else None
    except Exception:
        return None

def start_watcher():
    if watcher_pid():
        return
    if os.name == "nt":
        pyw = Path(sys.executable).with_name("pythonw.exe")
        exe = str(pyw if pyw.exists() else sys.executable)
        flags = dict(creationflags=0x00000008 | 0x08000000)  # DETACHED_PROCESS|CREATE_NO_WINDOW
    else:
        exe = sys.executable
        flags = dict(start_new_session=True)
    subprocess.Popen([exe, os.path.abspath(__file__), "watch"], **flags)

def stop_watcher():
    pid = watcher_pid()
    if not pid:
        return
    if os.name == "posix":
        os.kill(pid, signal.SIGTERM)
    else:
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)


# ---------- GUI ----------
def gui():
    import threading
    import tkinter as tk
    from tkinter import messagebox

    BG, PANEL, FG, MUTED = "#16161e", "#1e1e2a", "#e6e6ea", "#8a8a9a"
    ACCENT, DARK, GREEN, RED = "#d97757", "#33333f", "#7fd88f", "#e06c75"
    F = "TkDefaultFont"

    root = tk.Tk()
    root.title("Claude Session Guard")
    root.configure(bg=BG)
    root.resizable(False, False)
    box = {"after": None}

    w = tk.Frame(root, bg=BG, padx=22, pady=20); w.pack()
    head = tk.Frame(w, bg=BG); head.pack(anchor="w")
    tk.Label(head, text="●", bg=BG, fg=ACCENT, font=(F, 13)).pack(side="left", padx=(0, 8))
    tk.Label(head, text="Claude Session Guard", bg=BG, fg=FG, font=(F, 15, "bold")).pack(side="left")
    tk.Label(w, text="Respalda y vigila tu sesión de Claude Code",
             bg=BG, fg=MUTED, font=(F, 9)).pack(anchor="w", pady=(2, 14))

    card = tk.Frame(w, bg=PANEL, padx=16, pady=12); card.pack(fill="x")
    st_watch = tk.Label(card, text="", bg=PANEL, fg=FG, font=(F, 10, "bold")); st_watch.pack(anchor="w")
    st_info = tk.Label(card, text="", bg=PANEL, fg=MUTED, font=(F, 9), justify="left"); st_info.pack(anchor="w", pady=(4, 0))

    bf = tk.Frame(w, bg=BG); bf.pack(fill="x", pady=(14, 0))
    msg = tk.Label(w, text="", bg=BG, fg=MUTED, font=(F, 9), wraplength=320, justify="left")

    def setmsg(t, err=False):
        msg.config(text=t, fg=RED if err else MUTED)

    def mkbtn(text, color, cmd):
        b = tk.Button(bf, text=text, command=cmd, bg=color, fg="#ffffff",
                      activebackground=color, activeforeground="#ffffff",
                      relief="flat", bd=0, font=(F, 10), pady=8, cursor="hand2")
        b.pack(fill="x", pady=3)
        return b

    def do_backup():
        try:
            setmsg(backup())
        except Exception as e:
            setmsg(str(e), err=True)
        refresh()

    def do_restore():
        if not messagebox.askyesno("Restaurar",
                "Esto sobrescribe tus credenciales actuales con la última copia.\n"
                "Reinicia Claude Code después. ¿Continuar?"):
            return
        try:
            setmsg(restore())
        except Exception as e:
            setmsg(str(e), err=True)

    def do_keepalive():
        setmsg("Probando y renovando el token…")
        def work():
            ok, detail = keepalive()
            if ok:
                _touch_refresh()
            root.after(0, lambda: setmsg(("✓ " if ok else "✗ ") + detail, err=not ok))
        threading.Thread(target=work, daemon=True).start()

    def open_folder():
        DEST.mkdir(parents=True, exist_ok=True)
        if platform.system() == "Windows":
            os.startfile(DEST)  # noqa
        elif platform.system() == "Darwin":
            subprocess.run(["open", str(DEST)])
        else:
            subprocess.run(["xdg-open", str(DEST)])
        setmsg(f"Abriendo {DEST}")

    def toggle_watch():
        if watcher_pid():
            stop_watcher(); setmsg("Vigilancia detenida")
        else:
            start_watcher(); setmsg("Vigilancia iniciada")
        root.after(400, refresh)

    def refresh():
        if box["after"]:
            root.after_cancel(box["after"])
        active = watcher_pid() is not None
        dot, txt, col = ("●", "Vigilancia activa", GREEN) if active else ("○", "Vigilancia detenida", RED)
        st_watch.config(text=f"{dot}  {txt}", fg=col)
        bks = backups()
        last = bks[-1].name.replace("_", "  ") if bks else "—"
        st_info.config(text=f"Último respaldo:   {last}\nCopias guardadas:  {len(bks)}")
        btn_watch.config(text="Detener vigilancia" if active else "Iniciar vigilancia")
        box["after"] = root.after(4000, refresh)

    mkbtn("Respaldar ahora", ACCENT, do_backup)
    mkbtn("Probar / renovar token", DARK, do_keepalive)
    mkbtn("Restaurar el último", DARK, do_restore)
    mkbtn("Abrir carpeta de respaldos", DARK, open_folder)
    btn_watch = mkbtn("", DARK, toggle_watch)
    msg.pack(anchor="w", pady=(12, 0))

    refresh()
    root.mainloop()


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "gui"
    try:
        if cmd == "gui":
            gui()
        elif cmd == "backup":
            print(backup())
        elif cmd == "restore":
            print(restore(sys.argv[2] if len(sys.argv) > 2 else None))
        elif cmd == "check":
            check()
        elif cmd == "keepalive":
            ok, detail = keepalive()
            print(detail)
            sys.exit(0 if ok else 1)
        elif cmd == "watch":
            watch(int(sys.argv[2]) if len(sys.argv) > 2 else 60)
        else:
            print("uso: guard.py [gui|backup|restore [dir]|watch [seg]|check]", file=sys.stderr)
            sys.exit(1)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
