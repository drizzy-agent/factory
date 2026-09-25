"""Composable access to raw tmux commands."""

from typing import cast

from factory.jsonrpc import JsonObject
from factory.plugin import Plugin
from factory.tmux import OperationFailure
from factory.work import WorkContext, WorkFailure, WorkResult, WorkSuccess


class TmuxCommand:
    """Expose the tmux runtime as a single work unit."""

    name = "tmux.command"

    def run(self, input: JsonObject, context: WorkContext) -> WorkResult:
        """Run a non-empty argument vector without shell interpolation."""
        arguments = input.get("arguments")
        if (
            not isinstance(arguments, list)
            or not arguments
            or not all(isinstance(argument, str) for argument in arguments)
        ):
            return WorkFailure(-32602, "Invalid params")
        result = context.tmux.command(*cast(list[str], arguments))
        if isinstance(result, OperationFailure):
            return WorkFailure(
                -32000, "Runtime operation failed", {"message": result.message}
            )
        return WorkSuccess({"stdout": result.value})


PLUGIN = Plugin(name="tmux", units=(TmuxCommand(),))
