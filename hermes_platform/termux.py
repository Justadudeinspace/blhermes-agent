"""Fixed-prefix Bionic bundle environment for children with filtered environments."""
from __future__ import annotations

import json
from pathlib import Path

PREFIX = '/data/data/com.termux/files/usr'


def bundle_child_environment(root: Path) -> dict[str, str]:
    """Reconstruct package-owned loader paths; never forward the parent's loader overrides."""
    manifest = root / 'manifest.json'
    if not manifest.is_file():
        return {}
    try:
        data = json.loads(manifest.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as exc:
        raise RuntimeError('Packaged runtime manifest is unreadable; reinstall BLHermes with the package manager.') from exc
    if not isinstance(data, dict):
        raise RuntimeError('Packaged runtime manifest is malformed; reinstall BLHermes with the package manager.')
    if data.get('target') != 'linux-arm64-bionic':
        return {}
    libraries = [str(root / f'tools/{tool}' / PREFIX.lstrip('/') / 'lib')
                 for tool in ('python', 'node', 'ffmpeg')]
    libraries.extend((str(root / 'runtime-libs/lib'), PREFIX + '/lib'))
    return {'PREFIX': PREFIX, 'LD_LIBRARY_PATH': ':'.join(libraries), 'PYTHONDONTWRITEBYTECODE': '1'}


def packaged_child_environment() -> dict[str, str]:
    # Installed module is <bundle>/app/hermes_platform/termux.py. A source
    # checkout has no Bionic bundle manifest at this location and returns {}.
    return bundle_child_environment(Path(__file__).resolve().parents[2])
