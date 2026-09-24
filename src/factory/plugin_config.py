"""Plugin configuration parsed from factory.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


class PluginConfigError(Exception):
    """A factory.toml [plugins] configuration problem."""


@dataclass(frozen=True, slots=True)
class PluginConfig:
    """Optional plugins enabled through factory.toml.

    Both collections default to empty when the file or the [plugins] table
    is absent, which preserves Factory behavior without configuration.
    """

    enabled: tuple[str, ...]
    paths: tuple[Path, ...]

    @classmethod
    def load(cls, path: Path = Path("factory.toml")) -> PluginConfig:
        """Read plugin configuration from a TOML file.

        A missing file yields empty defaults. Invalid TOML or invalid
        field types raise PluginConfigError.
        """
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return cls((), ())
        return cls.from_toml(text, source=path)

    @classmethod
    def from_toml(
        cls, text: str, *, source: str | Path = "factory.toml"
    ) -> PluginConfig:
        """Parse plugin configuration from TOML text.

        A missing [plugins] table yields empty defaults. Invalid TOML or
        invalid field types raise PluginConfigError.
        """
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError as error:
            raise PluginConfigError(f"invalid TOML in {source}: {error}") from error
        plugins = data.get("plugins", {})
        if not isinstance(plugins, dict):
            raise PluginConfigError(f"[plugins] must be a table in {source}")
        return cls(
            enabled=_parse_enabled(plugins.get("enabled", []), source),
            paths=_parse_paths(plugins.get("paths", []), source),
        )


def _parse_enabled(value: object, source: str | Path) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise PluginConfigError(
            f"[plugins].enabled must be a list of plugin names in {source}"
        )
    names: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise PluginConfigError(
                f"[plugins].enabled must contain only plugin names in {source}"
            )
        names.append(item)
    return tuple(names)


def _parse_paths(value: object, source: str | Path) -> tuple[Path, ...]:
    if not isinstance(value, list):
        raise PluginConfigError(
            f"[plugins].paths must be a list of filesystem paths in {source}"
        )
    paths: list[Path] = []
    for item in value:
        if not isinstance(item, str):
            raise PluginConfigError(
                f"[plugins].paths must contain only filesystem paths in {source}"
            )
        paths.append(Path(item).expanduser())
    return tuple(paths)
