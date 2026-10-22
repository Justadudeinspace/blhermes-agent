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
