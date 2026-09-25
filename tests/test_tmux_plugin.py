"""Behavior tests for the core tmux work unit, without running tmux."""

import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from factory.command import CommandFailure, CommandResult, CommandSuccess
from factory.jsonrpc import JsonObject, JsonValue
from factory.notifications import NotificationLog
from factory.tmux import TmuxRuntime
from factory.work import WorkContext, WorkResult, WorkRunner, WorkUnit
from plugins.core.tmux import PLUGIN


class FakeCommandRunner:
    def __init__(self, result: CommandResult) -> None:
        self.result = result
        self.commands: list[tuple[str, ...]] = []

    def run(
        self, arguments: Sequence[str], *, input_text: str | None = None
    ) -> CommandResult:
        self.commands.append(tuple(arguments))
        return self.result


def _runner(
    result: CommandResult | None = None,
    units: tuple[WorkUnit, ...] = (),
) -> tuple[WorkRunner, FakeCommandRunner]:
    commands = FakeCommandRunner(
        CommandSuccess("output\n") if result is None else result
    )
    runtime = TmuxRuntime.create(commands)
    # Command execution never publishes notifications or opens this path.
    notifications = NotificationLog(Path("unused-notifications.jsonl"), [])
    return (
        WorkRunner.create(runtime, notifications, units=(*PLUGIN.units, *units)),
        commands,
    )


def _call(runner: WorkRunner, unit: str, input: JsonObject) -> object:
    request: JsonObject = {
        "jsonrpc": "2.0",
        "method": "work.run",
        "params": {"unit": unit, "input": input},
        "id": 1,
    }
    response = runner.protocol.handle(json.dumps(request).encode())
    assert response is not None
    return json.loads(response)


def test_plugin_exposes_only_tmux_command() -> None:
    assert PLUGIN.name == "tmux"
    assert [unit.name for unit in PLUGIN.units] == ["tmux.command"]
    runner, commands = _runner()
    response = runner.protocol.handle(b'{"jsonrpc":"2.0","method":"work.list","id":1}')
    assert response is not None
    assert "tmux.command" in json.loads(response)["result"]
    assert commands.commands == []


@pytest.mark.parametrize("stdout", ["output\n", ""])
def test_command_preserves_arguments_and_stdout(stdout: str) -> None:
    runner, commands = _runner(CommandSuccess(stdout))
    arguments: list[JsonValue] = [
        "display-popup",
        "-E",
        "my-ui --title 'a b'",
        "$(touch nope);",
        "",
    ]

    response = _call(runner, "tmux.command", {"arguments": arguments})

    assert response == {"jsonrpc": "2.0", "id": 1, "result": {"stdout": stdout}}
    assert commands.commands == [("tmux", *arguments)]


@pytest.mark.parametrize(
    "input",
    [
        {},
        {"arguments": None},
        {"arguments": []},
        {"arguments": "display-popup"},
        {"arguments": 1},
        {"arguments": {}},
        {"arguments": ["display-popup", 1]},
        {"arguments": [False]},
        {"arguments": [["display-popup"]]},
    ],
)
def test_invalid_arguments_do_not_execute(input: JsonObject) -> None:
    runner, commands = _runner()

    response = _call(runner, "tmux.command", input)

    assert response == {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {"code": -32602, "message": "Invalid params"},
    }
    assert commands.commands == []


def test_command_failure_becomes_work_failure() -> None:
    runner, commands = _runner(CommandFailure("no server running"))

    response = _call(runner, "tmux.command", {"arguments": ["list-sessions"]})

    assert response == {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32000,
            "message": "Runtime operation failed",
            "data": {"message": "no server running"},
        },
    }
    assert commands.commands == [("tmux", "list-sessions")]


def test_another_plugin_can_compose_tmux_command() -> None:
    class Popup:
        name = "example.popup"

        def run(self, input: JsonObject, context: WorkContext) -> WorkResult:
            return context.run(
                "tmux.command", {"arguments": ["display-popup", "-E", "my-ui"]}
            )

    runner, commands = _runner(units=(Popup(),))

    response = _call(runner, "example.popup", {})

    assert response == {"jsonrpc": "2.0", "id": 1, "result": {"stdout": "output\n"}}
    assert commands.commands == [("tmux", "display-popup", "-E", "my-ui")]
