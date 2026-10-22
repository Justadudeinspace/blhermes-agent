"""A Linux interpreter must never produce an Android runtime acceptance receipt."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.platforms("linux")
def test_glibc_interpreter_cannot_certify_android_runtime(tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts/termux/runtime_probe.py"
    prefix = tmp_path / "prefix"
    prefix.mkdir()
    result = subprocess.run([sys.executable, str(script)], cwd=tmp_path,
                            env={**os.environ, "PREFIX": str(prefix), "HERMES_HOME": str(prefix / "state")},
                            capture_output=True, text=True, check=False, timeout=30)
    assert result.returncode != 0
    assert "requires packaged Android/Bionic Python" in result.stderr
    assert "BIONIC_RUNTIME_CONTRACTS_OK" not in result.stdout
    assert not list(prefix.iterdir())
