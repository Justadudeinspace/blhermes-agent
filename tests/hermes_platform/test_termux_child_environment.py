"""Sealed Bionic runtime paths survive MCP filtering without forwarding secrets or loader overrides."""
import json
import os

import pytest

from hermes_platform.termux import bundle_child_environment


def test_only_bionic_bundle_supplies_fixed_prefix_child_environment(tmp_path):
    assert bundle_child_environment(tmp_path) == {}
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'target': 'linux-arm64'}))
    assert bundle_child_environment(tmp_path) == {}
    manifest.write_text(json.dumps({'target': 'linux-arm64-bionic'}))
    env = bundle_child_environment(tmp_path)
    assert env['PREFIX'] == '/data/data/com.termux/files/usr'
    assert env['PYTHONDONTWRITEBYTECODE'] == '1'
    assert str(tmp_path / 'runtime-libs/lib') in env['LD_LIBRARY_PATH'].split(':')
    assert str(tmp_path / 'tools/node/data/data/com.termux/files/usr/lib') in env['LD_LIBRARY_PATH'].split(':')


@pytest.mark.parametrize('consumer', ['mcp', 'execute_code'])
def test_filtered_children_use_package_loader_paths_without_parent_injection(tmp_path, monkeypatch, consumer):
    from hermes_platform import termux
    from tools.mcp_tool_transport import _stdio_launch
    from tools.code_execution_env import _scrub_child_env

    (tmp_path / 'manifest.json').write_text(json.dumps({'target': 'linux-arm64-bionic'}))
    monkeypatch.setattr(termux, 'packaged_child_environment', lambda: bundle_child_environment(tmp_path))
    monkeypatch.setenv('LD_LIBRARY_PATH', '/foreign/injected')
    monkeypatch.setenv('OPENAI_API_KEY', 'private-do-not-forward')
    builders = {'mcp': lambda: _stdio_launch({'command': '/private/bundle/python'})[1],
                'execute_code': lambda: _scrub_child_env(dict(os.environ), is_passthrough=lambda _: False)}
    env = builders[consumer]()
    assert '/foreign/injected' not in env['LD_LIBRARY_PATH']
    assert str(tmp_path / 'runtime-libs/lib') in env['LD_LIBRARY_PATH']
    assert 'OPENAI_API_KEY' not in env


def test_corrupted_package_manifest_is_actionable(tmp_path):
    (tmp_path / 'manifest.json').write_text('[]')
    with pytest.raises(RuntimeError, match='reinstall BLHermes'):
        bundle_child_environment(tmp_path)
