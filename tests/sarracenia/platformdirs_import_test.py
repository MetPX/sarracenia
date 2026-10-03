import sys
import types
from pathlib import Path


def _exec_sarracenia_init_with_features(features, modules):
    init_path = Path(__file__).parents[2] / "sarracenia" / "__init__.py"
    old_modules = {}
    for name, module in modules.items():
        old_modules[name] = sys.modules.get(name)
        sys.modules[name] = module

    namespace = {
        "__file__": str(init_path),
        "__name__": "sarracenia_platformdirs_test",
        "features": features,
    }
    lines = init_path.read_text().splitlines()
    start = next(index for index, line in enumerate(lines) if line.startswith("if features['humanize']['present']:"))
    end = next(index for index, line in enumerate(lines) if line.startswith('"""') and index > start)
    try:
        exec("\n".join(lines[start:end]), namespace)
    finally:
        for name, module in old_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    return namespace


def test_platformdirs_preferred_over_appdirs():
    platformdirs = types.SimpleNamespace(
        site_config_dir=lambda app, author: f"platform-site/{app}/{author}",
        user_config_dir=lambda app, author: f"platform-config/{app}/{author}",
        user_cache_dir=lambda app, author: f"platform-cache/{app}/{author}",
    )
    appdirs = types.SimpleNamespace(
        site_config_dir=lambda app, author: f"appdirs-site/{app}/{author}",
        user_config_dir=lambda app, author: f"appdirs-config/{app}/{author}",
        user_cache_dir=lambda app, author: f"appdirs-cache/{app}/{author}",
    )

    namespace = _exec_sarracenia_init_with_features(
        {
            'humanize': {'present': False},
            'platformdirs': {'present': True},
            'appdirs': {'present': True},
        },
        {'platformdirs': platformdirs, 'appdirs': appdirs},
    )

    assert namespace['site_config_dir']('sr3', 'MetPX') == 'platform-site/sr3/MetPX'
    assert namespace['user_config_dir']('sr3', 'MetPX') == 'platform-config/sr3/MetPX'
    assert namespace['user_cache_dir']('sr3', 'MetPX') == 'platform-cache/sr3/MetPX'


def test_appdirs_used_when_platformdirs_missing():
    appdirs = types.SimpleNamespace(
        site_config_dir=lambda app, author: f"appdirs-site/{app}/{author}",
        user_config_dir=lambda app, author: f"appdirs-config/{app}/{author}",
        user_cache_dir=lambda app, author: f"appdirs-cache/{app}/{author}",
    )

    namespace = _exec_sarracenia_init_with_features(
        {
            'humanize': {'present': False},
            'platformdirs': {'present': False},
            'appdirs': {'present': True},
        },
        {'appdirs': appdirs},
    )

    assert namespace['site_config_dir']('sr3', 'MetPX') == 'appdirs-site/sr3/MetPX'
    assert namespace['user_config_dir']('sr3', 'MetPX') == 'appdirs-config/sr3/MetPX'
    assert namespace['user_cache_dir']('sr3', 'MetPX') == 'appdirs-cache/sr3/MetPX'
