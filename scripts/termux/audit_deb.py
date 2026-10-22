"""Inspect a Termux release archive without executing its payload (host check only)."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import tarfile
import tempfile


PREFIX = "data/data/com.termux/files/usr"
ROOT = PREFIX + "/lib/hermes-agent"
SYSTEM_LIBS = {"libc.so", "libm.so", "libdl.so", "liblog.so", "libandroid.so"}
NATIVE_PROGRAMS = {
    f"tools/{tool}/{PREFIX}/bin/{binary}"
    for tool, binary in (("python", "python3.14"), ("node", "node"), ("uv", "uv"), ("ffmpeg", "ffmpeg"))
} | {"tools/ripgrep/rg"}
LAUNCHERS = {"bin/hermes", "bin/hermes-agent", "bin/hermes-acp"}


def checked_name(name: str) -> str:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe archive path: {name}")
    return str(path)


def elf_facts(path: Path, executable: bool = False) -> tuple[set[str], set[str]]:
    result = subprocess.run(["readelf", "-W", "-h", "-l", "-d", "-V", str(path)],
                            capture_output=True, text=True, check=True, timeout=30)
    data = result.stdout
    if not re.search(r"Machine:\s+AArch64", data) or not re.search(r"Class:\s+ELF64", data):
        raise ValueError("ELF must be 64-bit AArch64")
    if "GLIBC_" in data or "ld-linux" in data:
        raise ValueError("glibc linkage in Android payload")
    interpreters = re.findall(r"Requesting program interpreter: (.*?)\]", data)
    if executable and not interpreters:
        raise ValueError("runtime executable lacks Android dynamic interpreter")
    if any(value != "/system/bin/linker64" for value in interpreters):
        raise ValueError(f"wrong Android ELF interpreter: {interpreters}")
    for paths in re.findall(r"\((?:RUNPATH|RPATH)\).*?\[(.*?)\]", data):
        for entry in paths.split(":"):
            if not (entry.startswith("$ORIGIN") or entry.startswith("${ORIGIN}")
                    or entry.startswith("/" + PREFIX + "/")):
                raise ValueError(f"host/relative ELF search path: {entry!r}")
    needed = set(re.findall(r"\(NEEDED\).*?\[(.*?)\]", data))
    sonames = set(re.findall(r"\(SONAME\).*?\[(.*?)\]", data))
    return needed, sonames


def inspect_member(archive, member, scratch, names, sizes, links, needed_by, providers):
    name = checked_name(member.name)
    if name == "." or (member.isdir() and PREFIX.startswith(name + "/")):
        return
    if not (name == PREFIX or name.startswith(PREFIX + "/")):
        raise ValueError(f"payload outside Termux prefix: {name}")
    if name in names:
        raise ValueError(f"duplicate archive path: {name}")
    names.add(name)
    if member.mode & 0o6000:
        raise ValueError(f"setuid/setgid payload: {name}")
    if member.issym() or member.islnk():
        target = member.linkname
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), target)) if member.issym() else checked_name(target)
        if target.startswith("/"):
            resolved = target.lstrip("/")
        if not resolved.startswith(PREFIX + "/"):
            raise ValueError(f"link escapes prefix: {name} -> {target}")
        links[name] = resolved
    elif member.isfile():
        sizes[name] = member.size
        source = archive.extractfile(member)
        magic = source.read(4)
        relative = name.removeprefix(ROOT + "/")
        if relative in NATIVE_PROGRAMS | LAUNCHERS and not member.mode & 0o111:
            raise ValueError(f"runtime command is not executable: {name}")
        if relative in NATIVE_PROGRAMS and magic != b"\x7fELF":
            raise ValueError(f"runtime command is not ELF: {name}")
        if relative in LAUNCHERS:
            header = magic + source.readline()
            if header.rstrip() != b"#!/data/data/com.termux/files/usr/bin/sh":
                raise ValueError(f"incorrect Termux launcher shebang: {name}")
        if magic == b"\x7fELF":
            with scratch.open("wb") as output:
                output.write(magic)
                while block := source.read(1 << 20):
                    output.write(block)
            try:
                needed, sonames = elf_facts(scratch, executable=relative in NATIVE_PROGRAMS)
            except (ValueError, subprocess.CalledProcessError) as exc:
                raise ValueError(f"{name}: {exc}") from exc
            providers.update(sonames | {PurePosixPath(name).name})
            needed_by[name] = needed
    elif not member.isdir():
        raise ValueError(f"unexpected archive member type: {name}")


def audit(deb: Path, expected_version: str | None = None) -> dict:
    metadata = subprocess.run(["dpkg-deb", "-f", str(deb)], capture_output=True,
                              text=True, check=True, timeout=30).stdout
    fields = dict(line.split(": ", 1) for line in metadata.splitlines() if ": " in line)
    if fields.get("Package") != "hermes-agent" or fields.get("Architecture") != "aarch64":
        raise ValueError("expected hermes-agent aarch64 package")
    if expected_version is not None and fields.get("Version") != expected_version:
        raise ValueError("package version differs from requested build")
    sizes: Counter = Counter()
    names: set[str] = set()
    providers: set[str] = set()
    needed_by: dict[str, set[str]] = {}
    links: dict[str, str] = {}
    process = subprocess.Popen(["dpkg-deb", "--fsys-tarfile", str(deb)], stdout=subprocess.PIPE)
    try:
        with tempfile.TemporaryDirectory(prefix="termux-elf-") as tmp:
            scratch = Path(tmp) / "object"
            with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
                for member in archive:
                    inspect_member(archive, member, scratch, names, sizes, links, needed_by, providers)
        if process.wait(timeout=30) != 0:
            raise ValueError("dpkg-deb could not read payload")
    finally:
        process.stdout.close()
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=30)
    for name, target in links.items():
        if target not in names:
            raise ValueError(f"dangling packaged link: {name} -> {target}")
        providers.add(PurePosixPath(name).name)
    for name, needed in needed_by.items():
        missing = needed - providers - SYSTEM_LIBS
        if missing:
            raise ValueError(f"{name}: unbundled SONAME dependencies: {sorted(missing)}")
    required = [*LAUNCHERS, *NATIVE_PROGRAMS, "venv/bin/python", "app/install-stamp.json",
                "app/.install_method", "native-wheels.json", "pm-runtime", "runtime-libs/lib"]
    for relative in required:
        if ROOT + "/" + relative not in names:
            raise ValueError(f"missing installed layout: {relative}")
    if not needed_by:
        raise ValueError("package has no native runtime")
    groups: Counter = Counter()
    site_packages: Counter = Counter()
    for name, size in sizes.items():
        relative = name.removeprefix(ROOT + "/")
        parts = relative.split("/")
        group = "/".join(parts[:2]) if parts[0] == "tools" else parts[0]
        groups[group] += size
        if "/site-packages/" in name:
            site_packages[name.split("/site-packages/", 1)[1].split("/", 1)[0]] += size
    with deb.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"validation": "HOST_ARTIFACT_INSPECTION_ONLY", "version": fields["Version"],
            "sha256": digest, "deb_bytes": deb.stat().st_size,
            "payload_bytes": sum(sizes.values()), "elf_objects": len(needed_by),
            "native_library_bytes": sum(sizes[name] for name in needed_by if ".so" in PurePosixPath(name).suffixes),
            "component_bytes": dict(groups), "largest_site_packages": site_packages.most_common(20),
            "largest_files": sizes.most_common(20)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deb", type=Path)
    parser.add_argument("--version")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = json.dumps(audit(args.deb, args.version), indent=2) + "\n"
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"Termux artifact inspection failed: {exc}\n")
    if args.report:
        args.report.write_text(report, encoding="utf-8")
    print(report, end="")


if __name__ == "__main__":
    main()
