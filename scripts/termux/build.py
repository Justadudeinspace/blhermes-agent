#!/usr/bin/env python3
"""Build the TUI and package a prepared bionic payload as a Termux .deb.

Use --prepare to stage pinned tools and build the wheelhouse first. Without
it, consume the prepared payload used by release CI.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.releases.commit_build import require_commit
from scripts.termux.deb_version import deb_version_for_tag


def prepare(repo: Path, payload: Path, revision: list[str]) -> None:
    from hermes_platform.host.facts import os_family, process_arch

    if os_family() != "linux" or process_arch() != "arm64":
        raise ValueError("--prepare requires a native aarch64 Linux build host (not phone-side Termux)")
    subprocess.run(["bash", "-c", 'for tool in git curl docker python3 node dpkg-deb jq readelf; do '
                    'command -v "$tool" >/dev/null || { echo "missing build tool: $tool" >&2; exit 1; }; done'],
                   check=True, timeout=30)
    subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL, timeout=30)
    # Both the wheelhouse and application are archived from the selected commit.
    # A dirty checkout would mix new build scripts with old packaged code.
    subprocess.run(["git", "-C", str(repo), "diff", "--exit-code", "HEAD"], check=True, timeout=30)
    payload.mkdir(parents=True, exist_ok=True)
    for tool in ("python", "node", "uv", "npm", "ffmpeg", "ripgrep"):
        subprocess.run(["bash", str(repo / "scripts/termux/termux_pkg_build.sh"),
                        tool, tool, str(payload)], cwd=repo, check=True, timeout=14400)
    subprocess.run([sys.executable, str(repo / "scripts/termux/stage_runtime_libs.py"), str(payload)],
                   cwd=repo, check=True, timeout=14400)
    subprocess.run(["bash", str(repo / "scripts/termux/termux_build.sh"),
                    "--repo", str(repo), "--out", str(payload), *revision], cwd=repo, check=True, timeout=14400)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    identity = parser.add_mutually_exclusive_group(required=True)
    identity.add_argument("--tag")
    identity.add_argument("--commit")
    parser.add_argument("--release-commit")
    parser.add_argument("--prepare", action="store_true", help="stage pinned runtimes and build Bionic wheels before assembly")
    args = parser.parse_args(argv)

    try:
        if args.tag is not None:
            deb_version_for_tag(args.tag)
        else:
            require_commit(args.commit)
        if args.release_commit is not None:
            if args.tag is None:
                parser.error("--release-commit requires --tag")
            require_commit(args.release_commit)
    except ValueError as exc:
        parser.error(str(exc))

    repo, payload, out = (path.resolve() for path in (args.repo, args.payload, args.out))
    paths = [("--repo", repo)] + ([] if args.prepare else [("--payload", payload)])
    for option, path in paths:
        if not path.is_dir():
            parser.error(f"{option} must name an existing directory: {path}")
    product = repo / ".build/termux/tui"
    revision = ["--tag", args.tag] if args.tag is not None else ["--commit", args.commit]
    if args.release_commit is not None:
        revision.extend(["--release-commit", args.release_commit])
    commands = [
        ["node", str(repo / "scripts/build/node-deps.mjs"),
         "--source", str(repo), "--workspace", "ui-tui"],
        ["node", str(repo / "scripts/build/tui.mjs"),
         "--source", str(repo), "--out", str(product)],
        ["bash", str(repo / "scripts/termux/build_deb.sh"),
         "--repo", str(repo), "--payload", str(payload), "--out", str(out),
         "--tui-product", str(product), *revision],
    ]
    try:
        if args.prepare:
            prepare(repo, payload, revision)
        for command in commands:
            subprocess.run(command, cwd=repo, check=True, timeout=14400)
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    except subprocess.TimeoutExpired as exc:
        print(f"termux build timed out after {exc.timeout}s: {exc.cmd}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"termux build: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"termux build: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
