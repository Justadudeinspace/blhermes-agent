"""Offline Bionic runtime contracts, run only by the installed interpreter."""
from __future__ import annotations

import asyncio
import ctypes
import json
import locale
import multiprocessing
import os
from pathlib import Path
import signal
import sqlite3
import ssl
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor


def child_value(queue) -> None:
    queue.put("Android Unicode: café 🦀")


async def async_value() -> str:
    return await asyncio.to_thread(lambda: "asyncio OK")


def probe(root: Path) -> dict:
    if sys.platform != "android" or not hasattr(sys, "getandroidapilevel"):
        raise RuntimeError("requires packaged Android/Bionic Python; a Linux host is not acceptance")
    if not Path(sys.prefix).is_relative_to(root) or not Path(sys.base_prefix).is_relative_to(root):
        raise RuntimeError(f"interpreter escaped package: {sys.prefix}, {sys.base_prefix}")
    if not any("site-packages" in path and Path(path).is_relative_to(root) for path in sys.path):
        raise RuntimeError("packaged site-packages missing")
    certificates = ssl.create_default_context().cert_store_stats()
    if not certificates["x509_ca"]:
        raise RuntimeError("no trusted TLS certificates; reinstall Termux ca-certificates")
    ctypes.CDLL("libc.so")
    text = "Android Unicode: café 🦀"
    with tempfile.TemporaryDirectory(prefix="hermes-runtime-") as tmp:
        file = Path(tmp) / "café.txt"
        file.write_text(text, encoding="utf-8")
        assert file.read_text(encoding="utf-8-sig") == text
    state = Path(os.environ["HERMES_HOME"])
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    database = state / "acceptance.sqlite"
    with sqlite3.connect(database) as db:
        db.execute("CREATE TABLE IF NOT EXISTS proof (value TEXT)")
        db.execute("INSERT INTO proof VALUES (?)", (text,))
    # A second interpreter verifies on-disk state, not a surviving connection.
    subprocess.run([sys.executable, "-c", "import sqlite3,sys; "
                    "db=sqlite3.connect(sys.argv[1]); "
                    "assert db.execute('SELECT value FROM proof').fetchone()[0] == sys.argv[2]",
                    str(database), text], check=True, timeout=30)
    with ThreadPoolExecutor(max_workers=1) as executor:
        assert executor.submit(lambda: text).result(timeout=10) == text
    assert asyncio.run(async_value()) == "asyncio OK"
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    child = context.Process(target=child_value, args=(queue,))
    child.start()
    try:
        assert queue.get(timeout=30) == text
        child.join(timeout=10)
        assert child.exitcode == 0
    finally:
        if child.is_alive():
            child.terminate()
            child.join(timeout=10)
        queue.close()
        queue.join_thread()
    received = []
    previous = signal.signal(signal.SIGINT, lambda *_: received.append(True))
    try:
        os.kill(os.getpid(), signal.SIGINT)
        assert received == [True]
    finally:
        signal.signal(signal.SIGINT, previous)
    return {"platform": sys.platform, "api_level": sys.getandroidapilevel(),
            "prefix": sys.prefix, "base_prefix": sys.base_prefix,
            "encoding": locale.getencoding(), "certificates": certificates,
            "tmpdir": tempfile.gettempdir(), "state": str(state),
            "network_tested": False, "provider_tested": False}


if __name__ == "__main__":
    print(json.dumps(probe(Path(os.environ["PREFIX"]) / "lib/hermes-agent"), indent=2))
    print("BIONIC_RUNTIME_CONTRACTS_OK")
