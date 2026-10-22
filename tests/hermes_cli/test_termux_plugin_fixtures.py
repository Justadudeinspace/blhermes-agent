"""Representative native-incompatible plugin failure must leave base discovery usable."""
from hermes_cli.plugins import PluginManager, PluginManifest


def test_native_incompatible_plugin_is_recorded_and_compatible_plugin_still_loads(tmp_path, monkeypatch):
    monkeypatch.setenv('HERMES_HOME', str(tmp_path))
    manager = PluginManager()
    fixtures = {
        'native-incompatible': "raise OSError('Android native dependency unavailable; choose a Bionic-compatible build')\n",
        'portable-fixture': 'def register(ctx):\n    pass\n',
    }
    try:
        for name, body in fixtures.items():
            directory = tmp_path / 'plugins' / name
            directory.mkdir(parents=True)
            (directory / '__init__.py').write_text(body)
            manager._load_plugin(PluginManifest(name=name, source='bundled', path=str(directory)))
        failed = manager._plugins['native-incompatible']
        assert not failed.enabled
        assert 'Bionic-compatible' in failed.error
        assert manager._plugins['portable-fixture'].enabled
    finally:
        manager.unload()
