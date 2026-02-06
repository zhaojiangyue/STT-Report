from stt.plugins.base import load_plugins, Plugin


def test_load_plugins_unknown_empty():
    plugins = load_plugins([], {})
    assert plugins == []


class DummyPlugin(Plugin):
    name = "dummy"
