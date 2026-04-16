"""Freddy CLI — main Typer app with command groups."""

import typer

from .commands import (
    audit, auto_draft, client, iteration, save, setup, sitemap, transcript,
)

app = typer.Typer(
    name="freddy",
    help="Freddy — distribution engineering agency CLI.",
    pretty_exceptions_enable=False,
    no_args_is_help=True,
)


class _GlobalState:
    human: bool = False


_state = _GlobalState()


@app.callback()
def main_callback(
    human: bool = typer.Option(False, "--human", help="Human-readable output instead of JSON"),
) -> None:
    """Freddy — distribution engineering agency CLI."""
    _state.human = human


def get_state() -> _GlobalState:
    return _state


# Command groups
app.add_typer(client.app, name="client")
app.add_typer(audit.app, name="audit")
app.add_typer(auto_draft.app, name="auto-draft")
app.add_typer(iteration.app, name="iteration")
app.add_typer(transcript.app, name="transcript")

# Standalone commands
app.command(name="setup")(setup.setup_command)
app.command(name="save")(save.save_command)
app.command(name="sitemap")(sitemap.sitemap_command)

if __name__ == "__main__":
    app()
