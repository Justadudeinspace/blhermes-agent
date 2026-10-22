"""Inspect real Debian archives; synthetic ELF is never a runnable release fixture."""
from __future__ import annotations

from pathlib import Path
import struct
import subprocess

import pytest

from scripts.termux.audit_deb import audit, checked_name, LAUNCHERS, NATIVE_PROGRAMS, ROOT


def package(tmp_path: Path) -> tuple[Path, Path]:
    stage = tmp_path / "stage"
    control = stage / "DEBIAN"
    control.mkdir(parents=True)
    (control / "control").write_text(
        "Package: hermes-agent\nVersion: 1.2.3\nArchitecture: aarch64\n"
        "Maintainer: Test\nDescription: synthetic archive inspection fixture\n")
    root = stage / ROOT
    for name in ("bin/hermes", "bin/hermes-acp", "venv/bin/python", "app/install-stamp.json",
                 "app/.install_method", "native-wheels.json"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture")
    (root / "pm-runtime").mkdir()
    (root / "runtime-libs/lib").mkdir(parents=True)
    # ELF64 AArch64 shared-object header, no code or dependencies.
    identity = b"\x7fELF\x02\x01\x01" + bytes(9)
    (root / "runtime-libs/lib/test.so").write_bytes(struct.pack(
        "<16sHHIQQQIHHHHHH", identity, 3, 183, 1, 0, 0, 0, 0, 64, 0, 0, 0, 0, 0))
    for name in LAUNCHERS:
        path = root / name
        path.write_text("#!/data/data/com.termux/files/usr/bin/sh\nexit 0\n")
        path.chmod(0o755)
    interpreter = b"/system/bin/linker64\0"
    executable = struct.pack("<16sHHIQQQIHHHHHH", identity, 3, 183, 1, 120, 64, 0,
                             0, 64, 56, 1, 0, 0, 0)
    executable += struct.pack("<IIQQQQQQ", 3, 4, 120, 0, 0, len(interpreter), len(interpreter), 1)
    executable += interpreter
    for name in NATIVE_PROGRAMS:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(executable)
        path.chmod(0o755)
    return stage, tmp_path / "fixture.deb"


def build(stage, deb):
    subprocess.run(["dpkg-deb", "--build", "--root-owner-group", str(stage), str(deb)],
                   check=True, capture_output=True)


@pytest.mark.platforms("linux")
def test_archive_inspection_measures_exact_bytes_and_rejects_escape(tmp_path):
    stage, deb = package(tmp_path)
    build(stage, deb)
    report = audit(deb, "1.2.3")
    assert report["validation"] == "HOST_ARTIFACT_INSPECTION_ONLY"
    assert report["deb_bytes"] == deb.stat().st_size
    assert report["component_bytes"]["runtime-libs"] == 64
    assert len(report["sha256"]) == 64
    (stage / ROOT / "bin/escape").symlink_to("/etc/passwd")
    build(stage, deb)
    with pytest.raises(ValueError, match="link escapes prefix"):
        audit(deb)
    (stage / ROOT / "bin/escape").unlink()
    (stage / ROOT / "bin/hermes").chmod(0o644)
    build(stage, deb)
    with pytest.raises(ValueError, match="not executable"):
        audit(deb)


@pytest.mark.platforms("linux")
def test_host_glibc_binary_is_rejected_inside_real_deb(tmp_path):
    stage, deb = package(tmp_path)
    (stage / ROOT / "runtime-libs/lib/test.so").write_bytes(Path("/usr/bin/true").read_bytes())
    build(stage, deb)
    with pytest.raises(ValueError, match="glibc|AArch64"):
        audit(deb)


@pytest.mark.parametrize("name", ["/etc/passwd", "../escape", "prefix/../../escape"])
def test_unsafe_member_names_are_rejected(name):
    with pytest.raises(ValueError, match="unsafe archive path"):
        checked_name(name)


@pytest.mark.platforms('linux')
@pytest.mark.parametrize('kind', ['cycle', 'fifo', 'setgid', 'dangling', 'absolute_escape'])
def test_adversarial_archive_rejected(tmp_path, kind):
    import os

    stage, deb = package(tmp_path)
    root = stage / ROOT
    path = root / 'bad'
    def cycle():
        path.symlink_to('other')
        (root / 'other').symlink_to('bad')

    def setgid():
        path.write_text('unexpected privilege')
        path.chmod(0o2644)

    operations = {'cycle': cycle, 'fifo': lambda: os.mkfifo(path), 'setgid': setgid,
                  'absolute_escape': lambda: path.symlink_to('/' + ROOT + '/../../../../../../etc/passwd'),
                  'dangling': lambda: path.symlink_to('missing')}
    operations[kind]()
    build(stage, deb)
    with pytest.raises(ValueError, match='cyclic|unexpected archive member|setuid/setgid|dangling|escapes prefix'):
        audit(deb)


@pytest.mark.parametrize('path', ['$ORIGINsuffix', '/data/data/com.termux/files/usr/../../outside', '/usr/lib', ''])
def test_elf_search_path_rejects_host_and_origin_lookalikes(path):
    from scripts.termux.audit_deb import valid_search_path

    assert not valid_search_path(path)


@pytest.mark.platforms('linux')
def test_release_manifest_measures_audited_artifact_without_promoting_device(tmp_path):
    from scripts.termux.release_manifest import summary

    stage, deb = package(tmp_path)
    build(stage, deb)
    result = summary('a' * 40, deb)
    assert result['deb_size'] == deb.stat().st_size
    assert result['audit_status'] == 'pass'
    assert result['device_validation_status'] == result['bionic_validation_status'] == 'pending'


@pytest.mark.platforms('linux')
def test_static_ripgrep_is_allowed_but_not_a_missing_python_loader(tmp_path):
    stage, deb = package(tmp_path)
    root = stage / ROOT
    identity = b'\x7fELF\x02\x01\x01' + bytes(9)
    executable = struct.pack('<16sHHIQQQIHHHHHH', identity, 2, 183, 1, 120, 64, 0,
                             0, 64, 56, 1, 0, 0, 0)
    executable += struct.pack('<IIQQQQQQ', 1, 5, 0, 0x400000, 0, 120, 120, 4096)
    (root / 'tools/ripgrep/rg').write_bytes(executable)
    build(stage, deb)
    assert audit(deb)['validation'] == 'HOST_ARTIFACT_INSPECTION_ONLY'
    (root / ('tools/python/' + ROOT.split('/lib/hermes-agent')[0] + '/bin/python3.14')).write_bytes(executable)
    build(stage, deb)
    with pytest.raises(ValueError, match='lacks Android dynamic interpreter'):
        audit(deb)


@pytest.mark.platforms('linux')
def test_release_summary_rejects_stale_audit_sidecar(tmp_path):
    import json
    from scripts.termux.release_manifest import summary

    stage, deb = package(tmp_path)
    build(stage, deb)
    sidecar = deb.with_name(deb.name + '.audit.json')
    report = audit(deb)
    sidecar.write_text(json.dumps(report))
    assert summary('a' * 40, deb)['audit_filename'] == sidecar.name
    report['sha256'] = '0' * 64
    sidecar.write_text(json.dumps(report))
    with pytest.raises(ValueError, match='sidecar'):
        summary('a' * 40, deb)


def test_origin_relative_search_paths_stay_inside_payload():
    from scripts.termux.audit_deb import valid_search_path

    assert valid_search_path('$ORIGIN/../lib', ROOT + '/bin')
    assert not valid_search_path('$ORIGIN/../../../../../../etc', ROOT + '/bin')


@pytest.mark.platforms('linux')
def test_malformed_payload_cli_reports_rejection_without_traceback(tmp_path):
    import gzip
    import sys
    from scripts.termux.stage_apt_repo import read_ar_entries
    from tests.termux_fixtures import build_deb

    deb = tmp_path / 'malformed.deb'
    build_deb(deb, {'Package': 'hermes-agent', 'Version': '1.2.3', 'Architecture': 'aarch64'})
    malformed = bytearray(b'!<arch>\n')
    for name, _, data in read_ar_entries(deb.read_bytes()):
        if name.startswith('data.tar'):
            data = gzip.compress(b'not a tar archive')
        malformed.extend(f"{name:<16}{0:<12}{0:<6}{0:<6}{'100644':<8}{len(data):<10}`\n".encode())
        malformed.extend(data + (b'\n' if len(data) % 2 else b''))
    deb.write_bytes(malformed)
    script = Path(__file__).resolve().parents[2] / 'scripts/termux/audit_deb.py'
    result = subprocess.run([sys.executable, str(script), str(deb)], capture_output=True,
                            text=True, timeout=30, check=False)
    assert result.returncode == 1
    assert 'Termux artifact inspection failed' in result.stderr
    assert 'Traceback' not in result.stderr
