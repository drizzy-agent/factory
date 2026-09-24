"""Factory's minimal plugin descriptor."""

from __future__ import annotations

from dataclasses import dataclass

from factory.work import WorkUnit


@dataclass(frozen=True, slots=True)
class Plugin:
    """A named, immutable bundle of work units shipped as a plugin.

    A plugin module exposes exactly one module-level value, e.g.::

        PLUGIN = Plugin(name="example", units=(ExampleUnit(),))
    """

    name: str
    units: tuple[WorkUnit, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Plugin name must be non-empty")
