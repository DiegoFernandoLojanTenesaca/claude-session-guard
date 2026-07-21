#!/usr/bin/env python3
"""Self-test mínimo (sin frameworks). Corre:  python3 test_guard.py
Ejercita backup / check / restore / creds-only / cifrado en un HOME temporal."""
import os
import sys
import json
import shutil
import tempfile
import subprocess
from pathlib import Path

GUARD = str(Path(__file__).resolve().parent / "guard.py")


def run(cmd, home, bk, extra=None):
    env = dict(os.environ, HOME=str(home), CLAUDE_BACKUP_DIR=str(bk))
    env.pop("CLAUDE_BACKUP_PASSPHRASE", None)
    if extra:
        env.update(extra)
    return subprocess.run([sys.executable, GUARD, *cmd], env=env, capture_output=True, text=True)


def seed(home, token="abc"):
    (home / ".claude").mkdir(parents=True, exist_ok=True)
    (home / ".claude" / ".credentials.json").write_text(
        json.dumps({"claudeAiOauth": {"accessToken": token}}))
    (home / ".claude" / ".last-cleanup").write_text("marker")
    (home / ".claude.json").write_text('{"cfg":1}')


def date_dirs(bk):
    return [p for p in bk.iterdir() if p.is_dir() and p.name[:4].isdigit()] if bk.exists() else []


def main():
    tmp = Path(tempfile.mkdtemp())
    home, bk = tmp / "home", tmp / "bk"
    home.mkdir()
    try:
        seed(home)
        r = run(["backup"], home, bk); assert r.returncode == 0, r.stderr
        assert len(date_dirs(bk)) == 1, "backup debe crear 1 carpeta con fecha"
        assert len(list(date_dirs(bk)[0].iterdir())) == 3, "deben respaldarse los 3 archivos"

        seed(home, token="")                       # token vacío
        run(["check"], home, bk)
        assert len(date_dirs(bk)) == 1, "check NO debe respaldar con token vacío"

        seed(home, token="RESTORED")
        run(["backup"], home, bk)                  # snapshot del estado bueno
        (home / ".claude" / ".credentials.json").write_text("{}")   # rompe el actual
        r = run(["restore"], home, bk); assert r.returncode == 0, r.stderr
        cred = json.loads((home / ".claude" / ".credentials.json").read_text())
        assert cred["claudeAiOauth"]["accessToken"] == "RESTORED", "restore debe recuperar el token"
        assert (home / ".claude.json").exists() and (home / ".claude" / ".last-cleanup").exists()
        assert (bk / "_restore_undo").exists(), "restore debe dejar red de seguridad reversible"

        (home / ".claude.json").write_text('{"cfg":"NEW"}')
        run(["restore", "--creds-only"], home, bk)
        assert json.loads((home / ".claude.json").read_text())["cfg"] == "NEW", \
            "--creds-only no debe tocar .claude.json"

        # cifrado (solo si hay openssl)
        if shutil.which("openssl"):
            home2, bk2 = tmp / "home2", tmp / "bk2"
            home2.mkdir(); seed(home2, token="SECRET")
            pw = {"CLAUDE_BACKUP_PASSPHRASE": "hunter2"}
            r = run(["backup"], home2, bk2, extra=pw); assert r.returncode == 0, r.stderr
            encs = list(date_dirs(bk2)[0].glob("*.enc"))
            assert len(encs) == 3, "con passphrase los snapshots deben ir cifrados (.enc)"
            (home2 / ".claude" / ".credentials.json").write_text("{}")
            r = run(["restore"], home2, bk2, extra=pw); assert r.returncode == 0, r.stderr
            cred = json.loads((home2 / ".claude" / ".credentials.json").read_text())
            assert cred["claudeAiOauth"]["accessToken"] == "SECRET", "restore debe descifrar"
            # sin passphrase no se puede restaurar un backup cifrado
            r = run(["restore"], home2, bk2); assert r.returncode != 0, "restore cifrado sin pass debe fallar"

        print("OK: todos los checks pasaron")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
