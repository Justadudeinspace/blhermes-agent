"""Emit a Termux build receipt. Unknown evidence stays null or pending."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import subprocess

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.releases.commit_build import require_commit
from scripts.termux.audit_deb import audit


def summary(commit: str, deb: Path | None = None) -> dict:
    require_commit(commit)
    result = dict(schema_version=1, source_commit=commit, package_name='hermes-agent',
                  package_version=None, architecture='aarch64', android_wheel_target='android_24_arm64_v8a',
                  deb_filename=None, deb_sha256=None, deb_size=None, installed_size=None,
                  audit_filename=None, audit_status='pending', bionic_validation_status='pending',
                  installed_validation_status='pending', device_validation_status='pending',
                  public_apt_status='not_provisioned', minimum_android_status='unqualified')
    if deb is not None:
        evidence = audit(deb)
        result.update(package_version=evidence['version'], deb_filename=deb.name,
                      deb_sha256=evidence['sha256'], deb_size=evidence['deb_bytes'],
                      installed_size=evidence['installed_size_kib'], audit_status='pass')
        sidecar = deb.with_name(deb.name + '.audit.json')
        if sidecar.is_file():
            recorded = json.loads(sidecar.read_text(encoding='utf-8-sig'))
            if recorded.get('sha256') != evidence['sha256'] or recorded.get('version') != evidence['version']:
                raise ValueError('audit sidecar does not describe this archive')
            result['audit_filename'] = sidecar.name
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--deb', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    # Only the assembler calls this after the mandatory container gate. Device
    # acceptance is intentionally never promotable by this host-side command.
    parser.add_argument('--container-validated', action='store_true')
    args = parser.parse_args()
    try:
        if args.container_validated and args.deb is None:
            raise ValueError('--container-validated requires --deb and successful build_deb.sh gates')
        report = summary(args.commit, args.deb)
        if args.container_validated:
            report.update(bionic_validation_status='pass', installed_validation_status='pass')
        args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(1, f'Release summary: {exc}\n')


if __name__ == '__main__':
    main()
