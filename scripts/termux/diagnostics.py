"""Read-only Termux facts. Never read credentials, conversations or application logs."""
from __future__ import annotations

import os
import json
import re
from pathlib import Path
import platform
import sys
import subprocess

PREFIX = Path('/data/data/com.termux/files/usr')
UPSTREAM = 'hermes-assets.nousresearch.com'


def stale_sources(prefix: Path) -> list[dict[str, str]]:
    """Report source filenames only; repository URLs can contain credentials."""
    apt = prefix / 'etc/apt'
    candidates = [apt / 'sources.list']
    directory = apt / 'sources.list.d'
    if directory.is_dir():
        candidates.extend(sorted(directory.glob('*.list')))
        candidates.extend(sorted(directory.glob('*.sources')))
    findings = []
    for path in candidates:
        if not path.is_file():
            continue
        try:
            active = [line for line in path.read_text(encoding='utf-8-sig').splitlines()
                      if line.strip() and not line.lstrip().startswith('#')]
            if any(UPSTREAM in line for line in active):
                findings.append({'file': str(path), 'action': 'Review this upstream Hermes source; disable only the identified entry before apt update.'})
        except (OSError, UnicodeError):
            findings.append({'file': str(path), 'action': 'Cannot read APT source; inspect locally.'})
    return findings


def environment_issues(env: dict[str, str]) -> list[str]:
    issues = []
    for name in ('HOME', 'PREFIX', 'TMPDIR', 'HERMES_HOME'):
        value = env.get(name, '') or (str(PREFIX) if name == 'PREFIX' else '')
        if name in ('TMPDIR', 'HERMES_HOME') and not value:
            continue
        if not value or not Path(value).is_absolute():
            issues.append(f'{name} must be an absolute private-storage path.')
    if (env.get('PREFIX') or str(PREFIX)) != str(PREFIX):
        issues.append(f'Only the standard com.termux prefix {PREFIX} is supported.')
    if not env.get('PATH'):
        issues.append('PATH is empty; include $PREFIX/bin.')
    return issues


def node_version(root: Path) -> str | None:
    prefix = root.parent.parent
    node = root / 'tools/node' / prefix.relative_to('/') / 'bin/node'
    env = {'PATH': str(prefix / 'bin'), 'LANG': 'C.UTF-8',
           'LD_LIBRARY_PATH': f"{root}/tools/node{prefix}/lib:{root}/runtime-libs/lib:{prefix}/lib"}
    try:
        output = subprocess.run([str(node), '--version'], env=env, capture_output=True,
                                text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    version = output.stdout.strip()
    return version if output.returncode == 0 and re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+', version) else None


def package_facts(root: Path) -> dict:
    result = {'source_commit': None, 'package_version': None, 'node_version': node_version(root), 'executables': {}}
    stamp = root / 'app/install-stamp.json'
    try:
        data = json.loads(stamp.read_text(encoding='utf-8-sig'))
        commit = data.get('commit', '')
        if isinstance(commit, str) and re.fullmatch(r'[a-f0-9]{40}', commit):
            result['source_commit'] = commit
    except (OSError, ValueError, AttributeError):
        pass  # A damaged/missing stamp is itself useful absence in the receipt.
    query = root.parent.parent / 'bin/dpkg-query'
    try:
        query_result = subprocess.run([str(query), '-W', '-f=${Version} ${Architecture}', 'hermes-agent'],
                                capture_output=True, text=True, timeout=10, check=False,
                                env={'PATH': str(query.parent), 'LANG': 'C.UTF-8'})
        if query_result.returncode == 0 and re.fullmatch(r'[0-9][A-Za-z0-9.+:~\-]* aarch64', query_result.stdout.strip()):
            result_version, result_arch = query_result.stdout.split()
            # Only dpkg's fixed version/architecture fields are eligible for sharing.
            metadata = {'package_version': result_version, 'architecture': result_arch}
        else:
            metadata = {}
    except (OSError, subprocess.SubprocessError):
        metadata = {}
    result.update(metadata)
    for name, relative in {'python': 'venv/bin/python', 'node': 'tools/node/data/data/com.termux/files/usr/bin/node',
                           'rg': 'tools/ripgrep/rg', 'hermes': 'bin/hermes'}.items():
        path = root / relative
        result['executables'][name] = {'path': str(path), 'executable': os.access(path, os.X_OK)}
    return result


def facts(prefix: Path) -> dict:
    from hermes_platform.host.facts import process_arch

    return {'package': package_facts(prefix / 'lib/hermes-agent'), 'python': platform.python_version(), 'platform': sys.platform,
            'machine': process_arch(),
            'android_api': sys.getandroidapilevel() if hasattr(sys, 'getandroidapilevel') else None,
            'environment_issues': environment_issues(dict(os.environ)),
            'upstream_sources': stale_sources(prefix),
            'collection_policy': 'No environment dump, config, keys, conversations or application logs collected.'}
