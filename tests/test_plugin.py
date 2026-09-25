"""Behavior tests for Factory's minimal plugin descriptor."""

from __future__ import annotations

import dataclasses

import pytest

from factory.jsonrpc import JsonObject
from factory.plugin import InvalidPluginError, Plugin
from factory.work import WorkContext, WorkResult, WorkUnit


class _ExampleUnit:
    @property
    def name(self) -> str:
        return "example.unit"

    def run(self, input: JsonObject, context: WorkContext) -> WorkResult:
        raise NotImplementedError


def test_plugin_exposes_name_and_units() -> None:
    unit = _ExampleUnit()
    plugin = Plugin(name="example", units=(unit,))
    assert plugin.name == "example"
    assert plugin.units == (unit,)


def test_plugin_accepts_empty_units() -> None:
    plugin = Plugin(name="example", units=())
    assert plugin.units == ()


def test_plugin_rejects_empty_name() -> None:
    with pytest.raises(InvalidPluginError, match="non-empty"):
        Plugin(name="", units=(_ExampleUnit(),))


def test_plugin_is_frozen() -> None:
    plugin = Plugin(name="example", units=())
    with pytest.raises(dataclasses.FrozenInstanceError):
        plugin.name = "other"  # type: ignore[misc]


def test_plugin_value_is_usable_as_work_unit() -> None:
    unit = _ExampleUnit()
    plugin = Plugin(name="example", units=(unit,))
    assert isinstance(plugin.units[0], WorkUnit)


def test_plugin_module_exposes_single_value() -> None:
    PLUGIN = Plugin(name="example", units=(_ExampleUnit(),))
    assert PLUGIN.name == "example"
    assert all(isinstance(unit, WorkUnit) for unit in PLUGIN.units)
