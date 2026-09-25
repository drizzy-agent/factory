"""Deterministic discovery of Factory's always-enabled core plugins."""

from collections.abc import Iterable
from pathlib import Path

from factory.plugin import Plugin, PluginError
from factory.plugin_loader import load_plugin
from factory.work import WorkUnit


class CorePluginError(PluginError):
    """Base class for core-plugin discovery errors."""


class CorePluginDirectoryError(CorePluginError):
    """Raised when the core directory cannot be read."""


class DuplicatePluginError(CorePluginError):
    """Raised when core plugins declare the same name."""


def load_core_plugins(path: Path) -> tuple[Plugin, ...]:
    """Load direct, public Python files in filename order."""
    try:
        paths = sorted(
            child
            for child in path.iterdir()
            if child.suffix == ".py"
            and not child.name.startswith("_")
            and child.is_file()
        )
    except OSError as error:
        raise CorePluginDirectoryError(f"Cannot read core plugins at {path}") from error

    plugins: list[Plugin] = []
    names: set[str] = set()
    for file in paths:
        plugin = load_plugin(file)
        if plugin.name in names:
            raise DuplicatePluginError(f"Duplicate core plugin name: {plugin.name}")
        names.add(plugin.name)
        plugins.append(plugin)
    return tuple(plugins)


def plugin_units(plugins: Iterable[Plugin]) -> tuple[WorkUnit, ...]:
    """Flatten plugins in discovery order for WorkRunner registration."""
    return tuple(unit for plugin in plugins for unit in plugin.units)
