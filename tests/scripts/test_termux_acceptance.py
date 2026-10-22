"""Offline acceptance must preserve private state and report unproven gates honestly."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.termux.diagnostics import environment_issues, stale_sources
from scripts.termux.release_manifest import summary


def test_stale_source_detection_never_changes_or_exposes_source(tmp_path):
    directory = tmp_path / 'etc/apt/sources.list.d'
    directory.mkdir(parents=True)
    stale = directory / 'hermes-agent.list'
    text = 'deb https://user:private@hermes-assets.nousresearch.com/releases/termux/stable ./\n'
    stale.write_text(text)
    (directory / 'unrelated.list').write_text('deb https://example.com stable main\n')
    rows = stale_sources(tmp_path)
    assert [r['file'] for r in rows] == [str(stale)]
    assert 'private' not in json.dumps(rows)
    assert stale.read_text() == text
    stale.write_text('# ' + text)
    assert stale_sources(tmp_path) == []


@pytest.mark.parametrize('name', ['HOME', 'PREFIX', 'TMPDIR', 'HERMES_HOME'])
def test_malformed_environment_has_actionable_diagnostic(name):
    env = {'HOME': '/private/home', 'PREFIX': '/data/data/com.termux/files/usr', 'PATH': '/bin'}
    env[name] = 'relative'
    assert any(name in issue for issue in environment_issues(env))
    if name == 'PREFIX':
        from scripts.termux.device_acceptance import collect

        with pytest.raises(ValueError, match='PREFIX must be absolute'):
            collect(Path('relative'), run_validator=False)


def test_no_artifact_receipt_does_not_invent_measurements():
    report = summary('a' * 40)
    for key in ('deb_filename', 'package_version', 'deb_sha256', 'deb_size', 'installed_size', 'audit_filename'):
        assert report[key] is None
    for key in ('audit_status', 'bionic_validation_status', 'installed_validation_status', 'device_validation_status'):
        assert report[key] == 'pending'


@pytest.mark.platforms('linux')
def test_host_refusal_bundle_excludes_credentials_and_private_logs(tmp_path):
    script = Path(__file__).resolve().parents[2] / 'scripts/termux/device_acceptance.py'
    output = tmp_path / 'receipt.json'
    env = {**os.environ, 'OPENAI_API_KEY': 'DO_NOT_COLLECT', 'PREFIX': str(tmp_path)}
    result = subprocess.run([sys.executable, str(script), '--safe', '--output', str(output)],
                            env=env, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 1
    report = json.loads(output.read_text())
    assert report['checks']['environment']['status'] == 'FAIL'
    assert 'DO_NOT_COLLECT' not in output.read_text() + result.stdout + result.stderr
    assert output.stat().st_mode & 0o777 == 0o600
    before = output.read_bytes()
    result = subprocess.run([sys.executable, str(script), '--output', str(output)], env=env,
                            capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 1
    assert output.read_bytes() == before


def test_apt_index_preserves_dependency_ownership(tmp_path):
    from scripts.termux.stage_apt_repo import stage
    from tests.termux_fixtures import build_deb

    pool = tmp_path / 'pool'
    pool.mkdir()
    fields = {'Package': 'hermes-agent', 'Version': '1.2.3', 'Architecture': 'aarch64',
              'Depends': 'ca-certificates', 'Breaks': 'example (<< 1)'}
    build_deb(pool / 'fixture.deb', fields)
    assert stage(pool, tmp_path / 'out', 'hermes-stable', None) == 3
    index = (tmp_path / 'out/dists/hermes-stable/main/binary-aarch64/Packages').read_text()
    assert 'Depends: ca-certificates\n' in index
    assert 'Breaks: example (<< 1)\n' in index


def test_real_offline_mcp_fixture_and_shutdown(tmp_path):
    script = Path(__file__).resolve().parents[2] / 'scripts/termux/mcp_probe.py'
    result = subprocess.run([sys.executable, str(script)], cwd=tmp_path,
                            capture_output=True, text=True, timeout=45, check=False)
    assert result.returncode == 0, result.stderr
    assert 'MCP_LOCAL_STDIO_OK' in result.stdout


@pytest.mark.parametrize('tail', [b'partial', b'x' * 60])
def test_apt_stager_rejects_malformed_ar_members(tail):
    from scripts.termux.stage_apt_repo import StageError, read_ar_entries

    with pytest.raises(StageError, match='ar'):
        list(read_ar_entries(b'!<arch>\n' + tail))


def test_diagnostic_versions_do_not_collect_child_errors_or_inherit_keys(tmp_path, monkeypatch):
    from scripts.termux.diagnostics import node_version

    def version(argv, **kwargs):
        assert 'OPENAI_API_KEY' not in kwargs['env']
        return subprocess.CompletedProcess(argv, 1, 'private stdout', 'private stderr')

    monkeypatch.setattr(subprocess, 'run', version)
    assert node_version(tmp_path / 'prefix/lib/hermes-agent') is None
