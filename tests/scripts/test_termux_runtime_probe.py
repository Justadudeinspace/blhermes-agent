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


def test_tls_configuration_errors_are_actionable(monkeypatch):
    import ssl
    from scripts.termux.runtime_probe import certificate_probe

    def unavailable():
        raise ssl.SSLError('bad certificate file')

    monkeypatch.setattr(ssl, 'create_default_context', unavailable)
    with pytest.raises(RuntimeError, match='ca-certificates.*SSL_CERT_FILE'):
        certificate_probe()


def test_empty_ca_store_is_not_a_tls_pass(monkeypatch):
    import ssl
    from types import SimpleNamespace
    from scripts.termux.runtime_probe import certificate_probe

    monkeypatch.setattr(ssl, 'create_default_context', lambda: SimpleNamespace(cert_store_stats=lambda: {'x509_ca': 0}))
    with pytest.raises(RuntimeError, match='no trusted TLS certificates'):
        certificate_probe()


def test_compression_hash_and_readline_runtime_contract():
    from scripts.termux.runtime_probe import stdlib_probe

    stdlib_probe()
