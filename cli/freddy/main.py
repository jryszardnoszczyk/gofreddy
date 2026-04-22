"""Freddy CLI — main Typer app with command groups."""

import typer

from .commands import (
    audit, auth, auto_draft, client, competitive, detect, digest, evaluate, fixture,
    iteration, monitor, query_monitor, save, scrape, search_ads, search_content,
    search_mentions, seo, session, setup, sitemap, transcript, trends, visibility,
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
app.add_typer(auth.app, name="auth")
app.add_typer(auto_draft.app, name="auto-draft")
app.add_typer(iteration.app, name="iteration")
app.add_typer(session.app, name="session")
app.add_typer(transcript.app, name="transcript")

# Autoresearch command groups (ported from freddy)
app.add_typer(evaluate.app, name="evaluate")
app.add_typer(monitor.app, name="monitor")
app.add_typer(digest.app, name="digest")
app.add_typer(competitive.app, name="competitive")
app.add_typer(seo.app, name="seo")
app.add_typer(fixture.app, name="fixture")

# Standalone commands
app.command(name="setup")(setup.setup_command)
app.command(name="save")(save.save_command)
app.command(name="sitemap")(sitemap.sitemap_command)

# Autoresearch standalone commands (ported from freddy)
app.command(name="scrape")(scrape.scrape_command)
app.command(name="detect")(detect.detect_command)
app.command(name="visibility")(visibility.visibility_command)
app.command(name="search-ads")(search_ads.search_ads_command)
app.command(name="query-monitor")(query_monitor.query_monitor_command)
app.command(name="search-content")(search_content.search_content_command)
app.command(name="search-mentions")(search_mentions.search)
app.command(name="trends")(trends.trends)

if __name__ == "__main__":
    app()
