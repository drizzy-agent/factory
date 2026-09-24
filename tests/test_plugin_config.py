"""Behavior tests for factory.toml plugin configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from factory.plugin_config import PluginConfig, PluginConfigError


def test_load_missing_file_returns_empty_defaults(tmp_path: Path) -> None:
    config = PluginConfig.load(tmp_path / "factory.toml")
    assert config == PluginConfig(enabled=(), paths=())


def test_load_reads_plugins_table(tmp_path: Path) -> None:
    path = tmp_path / "factory.toml"
    path.write_text(
        '[plugins]\nenabled = ["github"]\npaths = ["~/plugins"]\n', encoding="utf-8"
    )
    config = PluginConfig.load(path)
    assert config.enabled == ("github",)
    assert config.paths == (Path("~/plugins").expanduser(),)


def test_from_toml_missing_plugins_table_returns_empty_defaults() -> None:
    config = PluginConfig.from_toml("[server]\nport = 8080\n")
    assert config.enabled == ()
    assert config.paths == ()


def test_from_toml_empty_plugins_table_returns_empty_defaults() -> None:
    config = PluginConfig.from_toml("[plugins]\n")
    assert config.enabled == ()
    assert config.paths == ()


def test_from_toml_parses_enabled_and_paths() -> None:
    config = PluginConfig.from_toml(
        "[plugins]\n"
        'enabled = ["github", "my-plugin"]\n'
        'paths = ["~/.config/factory/plugins", "/opt/plugins"]\n'
    )
    assert config.enabled == ("github", "my-plugin")
    assert config.paths == (
        Path("~/.config/factory/plugins").expanduser(),
        Path("/opt/plugins"),
    )


def test_from_toml_expands_bare_tilde_to_home() -> None:
    config = PluginConfig.from_toml('[plugins]\npaths = ["~"]\n')
    assert config.paths == (Path.home(),)


def test_from_toml_ignores_unknown_keys() -> None:
    config = PluginConfig.from_toml('[plugins]\nenabled = []\nfuture = "yes"\n')
    assert config == PluginConfig(enabled=(), paths=())


def test_from_toml_rejects_invalid_toml() -> None:
    with pytest.raises(PluginConfigError, match="invalid TOML"):
        PluginConfig.from_toml("[plugins\n")


def test_from_toml_rejects_non_table_plugins() -> None:
    with pytest.raises(PluginConfigError, match=r"\[plugins\] must be a table"):
        PluginConfig.from_toml('plugins = "github"\n')


def test_from_toml_rejects_non_list_enabled() -> None:
    with pytest.raises(PluginConfigError, match=r"\[plugins\]\.enabled must be a list"):
        PluginConfig.from_toml('[plugins]\nenabled = "github"\n')


def test_from_toml_rejects_non_string_enabled_item() -> None:
    with pytest.raises(PluginConfigError, match="must contain only plugin names"):
        PluginConfig.from_toml("[plugins]\nenabled = [42]\n")


def test_from_toml_rejects_non_list_paths() -> None:
    with pytest.raises(PluginConfigError, match=r"\[plugins\]\.paths must be a list"):
        PluginConfig.from_toml('[plugins]\npaths = "~/plugins"\n')


def test_from_toml_rejects_non_string_path_item() -> None:
    with pytest.raises(PluginConfigError, match="must contain only filesystem paths"):
        PluginConfig.from_toml("[plugins]\npaths = [true]\n")


def test_load_rejects_invalid_toml(tmp_path: Path) -> None:
    path = tmp_path / "factory.toml"
    path.write_text("[plugins\n", encoding="utf-8")
    with pytest.raises(PluginConfigError, match="invalid TOML"):
        PluginConfig.load(path)
