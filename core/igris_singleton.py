"""Guardia de una sola marcha Igris por cuartel."""
from __future__ import annotations

import atexit
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any


_ROOT = Path(__file__).resolve().parents[1]
_LOCK_DEFAULT = _ROOT / "data" / "arise_igris.lock"


def _pid_vivo(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        import psutil

        return bool(psutil.pid_exists(pid))
    except Exception:
        pass
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False


class GuardiaIgris:
    def __init__(
        self,
        path: str | Path | None = None,
        *,
        revisar_procesos: bool = True,
    ) -> None:
        self.path = Path(path) if path else _LOCK_DEFAULT
        self.token = uuid.uuid4().hex
        self.adquirida = False
        self.revisar_procesos = bool(revisar_procesos)

    def _otra_marcha(self) -> dict[str, Any] | None:
        if not self.revisar_procesos:
            return None
        try:
            import psutil
        except Exception:
            return None
        propio = os.getpid()
        for proc in psutil.process_iter(["pid", "cmdline"]):
            try:
                pid = int(proc.info.get("pid") or 0)
                cmd = " ".join(proc.info.get("cmdline") or []).replace("\\", "/").lower()
            except Exception:
                continue
            if pid != propio and "scripts/arise_igris.py" in cmd:
                return {"pid": pid, "cmd": cmd, "fuente": "proceso"}
        return None

    def _leer(self) -> dict[str, Any]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
        except Exception:
            return {}

    def adquirir(self) -> tuple[bool, dict[str, Any]]:
        otra = self._otra_marcha()
        if otra:
            return False, otra
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "pid": os.getpid(),
            "token": self.token,
            "creado_ts": time.time(),
        }
        for _ in range(2):
            try:
                fd = os.open(
                    self.path,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                )
            except FileExistsError:
                actual = self._leer()
                pid = int(actual.get("pid") or 0)
                if _pid_vivo(pid):
                    return False, actual
                try:
                    self.path.unlink()
                except OSError:
                    return False, actual
                continue
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False)
                fh.write("\n")
            self.adquirida = True
            atexit.register(self.liberar)
            return True, payload
        return False, self._leer()

    def liberar(self) -> None:
        if not self.adquirida:
            return
        actual = self._leer()
        if str(actual.get("token") or "") == self.token:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
        self.adquirida = False
