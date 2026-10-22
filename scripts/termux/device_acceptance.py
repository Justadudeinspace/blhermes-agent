"""Non-destructive offline acceptance driver and shareable facts-only failure bundle."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.termux.diagnostics import PREFIX, facts


def check(argv: list[str], env: dict[str, str], cwd: Path, timeout: int = 900) -> dict:
    """Execute only fixed offline checks in isolated state; never include child output."""
    child = None
    try:
        child = subprocess.Popen(argv, env=env, cwd=cwd, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 start_new_session=True)
        code = child.wait(timeout=timeout)
        return {'status': 'PASS' if code == 0 else 'FAIL', 'exit_code': code}
    except subprocess.TimeoutExpired:
        return {'status': 'FAIL', 'reason': f'Timed out after {timeout}s'}
    except OSError:
        return {'status': 'FAIL', 'reason': 'Cannot execute installed command; check package installation and executable modes.'}
    finally:
        if child is not None and child.poll() is None:
            from scripts.termux.validate_installed import stop_child_tree

            stop_child_tree(child)


def collect(prefix: Path, *, run_validator: bool) -> dict:
    if not prefix.is_absolute():
        raise ValueError(f'PREFIX must be absolute; use {PREFIX}')
    report = {'schema_version': 1, 'facts': facts(prefix), 'checks': {}}
    checks = report['checks']
    if sys.platform != 'android' or not hasattr(sys, 'getandroidapilevel') or prefix != PREFIX:
        checks['environment'] = {'status': 'FAIL', 'reason': 'Requires real standard-prefix Termux Android Python; host results are not device evidence.'}
        return report
    checks['environment'] = {'status': 'FAIL' if report['facts']['environment_issues'] else 'PASS'}
    root = prefix / 'lib/hermes-agent'
    with tempfile.TemporaryDirectory(prefix='blhermes-acceptance-', dir=prefix / 'tmp') as tmp:
        home = Path(tmp)
        env = {'HOME': tmp, 'HERMES_HOME': str(home / 'state'), 'PREFIX': str(prefix),
               'TMPDIR': str(prefix / 'tmp'), 'PATH': str(prefix / 'bin'),
               'LANG': 'C.UTF-8', 'TERM': 'xterm-256color',
               'PYTHONPATH': str(root / 'app'),
               'PYTHONPYCACHEPREFIX': str(home / 'pycache'),
               'LD_LIBRARY_PATH': ':'.join(str(root / f'tools/{tool}' / prefix.relative_to('/') / 'lib')
                                          for tool in ('python', 'node', 'ffmpeg')) + f':{root}/runtime-libs/lib:{prefix}/lib'}
        package = report['facts']['package']
        checks['package_identity'] = {'status': 'PASS' if package.get('architecture') == 'aarch64' and package['package_version'] else 'FAIL'}
        checks['cli_version'] = check([str(prefix / 'bin/hermes'), '--version'], env, home)
        checks['installed_validator'] = (check([str(root / 'venv/bin/python'), '-B',
                                               str(root / 'app/scripts/termux/validate_installed.py')], env, home)
                                         if run_validator else {'status': 'SKIP', 'reason': 'Facts only; rerun with --safe.'})
    for name in ('authenticated_provider', 'android_lifecycle', 'signed_upgrade', 'optional_permissions'):
        checks[name] = {'status': 'SKIP', 'reason': 'Operator acceptance worksheet required.'}
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--safe', action='store_true', help='run offline installed checks in disposable private state')
    parser.add_argument('--output', type=Path, required=True, help='new private JSON receipt; existing files are never overwritten')
    args = parser.parse_args(argv)
    try:
        report = collect(Path(os.environ.get('PREFIX') or PREFIX), run_validator=args.safe)
        with args.output.open('x', encoding='utf-8') as stream:
            os.chmod(args.output, 0o600)
            json.dump(report, stream, indent=2)
            stream.write('\n')
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Acceptance collection failed: {exc}\nUse a new output file in writable private Termux storage.\n')
    print(f'Receipt: {args.output}; no private application logs collected.')
    return int(any(row['status'] == 'FAIL' for row in report['checks'].values()))


if __name__ == '__main__':
    raise SystemExit(main())
