import argparse
from abc import ABC
from threading import Event

from debutizer.commands import Command


def test_cleanup_hooks_run():
    hook_run = Event()

    class HookCommand(NoArgsCommand):
        def behavior(self, args: argparse.Namespace) -> None:
            self.cleanup_hooks.append(hook_run.set)

    command = HookCommand()
    command.run()

    assert hook_run.is_set()


def test_cleanup_hooks_ignore_errors():
    class FailingCommand(NoArgsCommand):
        def behavior(self, args: argparse.Namespace) -> None:
            self.cleanup_hooks.append(self._do_failing_action)

        def _do_failing_action(self) -> None:
            raise RuntimeError("Oh no!")

    command = FailingCommand()
    command.run()


class NoArgsCommand(Command, ABC):
    """A version of Command that avoids defining an ArgumentParser, since that messes
    with pytest's own ArgumentParser.
    """

    def __init__(self):
        self.parser = None

    def parse_args(self) -> argparse.Namespace:
        return argparse.Namespace()
