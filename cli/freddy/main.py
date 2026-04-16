"""Freddy CLI — main Typer app with command groups."""

import typer

from .api import set_global_timeout
from .commands import (
    accounts, analytics, articles, auth, auto_draft, calendar, competitive, content, creator,
    detect, digest, evaluate, iteration, media, monitor, newsletter, query_monitor, rank, save,
    scrape, search_ads, search_content, search_mentions, seo, session, setup, sitemap,
    transcript, trends, usage, video, visibility, write,
)
from .commands import publish as publish_cmd

app = typer.Typer(
    name="freddy",
    help="Freddy platform CLI for AI marketing agency operations.",
    pretty_exceptions_enable=False,
    no_args_is_help=True,
)


# ── Global options via callback ─────────────────────────────────────────────


class _GlobalState:
    human: bool = False
    timeout_seconds: float | None = None


_state = _GlobalState()


@app.callback()
def main_callback(
    human: bool = typer.Option(False, "--human", help="Human-readable output instead of JSON"),
    timeout: float | None = typer.Option(
        None,
        "--timeout",
        help="Override HTTP read timeout in seconds (applies to all commands as defense-in-depth against backend stalls)",
    ),
) -> None:
    """Freddy platform CLI."""
    _state.human = human
    _state.timeout_seconds = timeout
    set_global_timeout(timeout)


def get_state() -> _GlobalState:
    return _state


# ── Command groups ──────────────────────────────────────────────────────────

app.add_typer(accounts.app, name="accounts")
app.add_typer(auth.app, name="auth")
app.add_typer(publish_cmd.app, name="publish")
app.add_typer(session.app, name="session")
app.add_typer(creator.app, name="creator")
app.add_typer(video.app, name="video")
app.add_typer(content.app, name="content")
app.add_typer(usage.app, name="usage")
app.add_typer(transcript.app, name="transcript")
app.add_typer(iteration.app, name="iteration")

# Standalone commands (not grouped)
app.command(name="setup")(setup.setup_command)
app.command(name="scrape")(scrape.scrape_command)
app.command(name="detect")(detect.detect_command)
app.command(name="visibility")(visibility.visibility_command)
app.command(name="search-ads")(search_ads.search_ads_command)
app.command(name="query-monitor")(query_monitor.query_monitor_command)
app.command(name="search-content")(search_content.search_content_command)
app.command(name="save")(save.save_command)
app.add_typer(evaluate.app, name="evaluate")
app.add_typer(auto_draft.app, name="auto-draft")

# Monitoring digest commands
app.add_typer(monitor.app, name="monitor")
app.add_typer(digest.app, name="digest")
app.add_typer(analytics.app, name="analytics")
app.add_typer(articles.app, name="articles")
app.add_typer(calendar.app, name="calendar")
app.add_typer(competitive.app, name="competitive")
app.add_typer(media.app, name="media")
app.add_typer(newsletter.app, name="newsletter")
app.add_typer(rank.app, name="rank")
app.add_typer(seo.app, name="seo")
app.add_typer(write.app, name="write")
app.command(name="sitemap")(sitemap.sitemap_command)
app.command(name="search-mentions")(search_mentions.search)
app.command(name="trends")(trends.trends)

if __name__ == "__main__":
    app()
