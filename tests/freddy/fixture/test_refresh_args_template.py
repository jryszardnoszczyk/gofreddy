"""Tests for the ``args_template`` + ``arg_for_cache_key`` fields in
sources.json and the refresh-side arg-assembly that consumes them.

Closes the refresh-CLI-signature-mismatch bug (2026-04-23-001): previously
all 5 sources were declared with ``args_from: ["context"]`` which only
worked for CLIs that took a single positional arg. Visibility, search-ads,
and search-content all take flags; refresh would pass ``fixture.context``
as a positional and the CLI rejected it.

Every source in the updated sources.json now ships with an
``args_template`` list describing the CLI signature explicitly. This test
pins the resolver behavior.
"""
from __future__ import annotations

import pytest

from cli.freddy.fixture.refresh import (
    _assemble_cli_args,
    _resolve_ref,
    _load_sources_config,
)
from cli.freddy.fixture.schema import FixtureSpec


def _fx(client: str = "c", context: str = "ctx", env=None) -> FixtureSpec:
    return FixtureSpec(
        fixture_id="fx",
        client=client,
        context=context,
        version="1.0",
        max_iter=1,
        timeout=60,
        anchor=False,
        env=dict(env or {}),
    )


# --- _resolve_ref --------------------------------------------------------


def test_resolve_ref_from_context():
    assert _resolve_ref(_fx(context="hello"), {"from": "context"}) == "hello"


def test_resolve_ref_from_client():
    assert _resolve_ref(_fx(client="bmw"), {"from": "client"}) == "bmw"


def test_resolve_ref_from_env_prefix():
    fx = _fx(env={"MY_KEY": "value-a"})
    assert _resolve_ref(fx, {"from": "env.MY_KEY"}) == "value-a"


def test_resolve_ref_fallback_from():
    fx = _fx(client="bmw", env={})  # MY_KEY absent
    spec = {"from": "env.MY_KEY", "fallback_from": "client"}
    assert _resolve_ref(fx, spec) == "bmw"


def test_resolve_ref_default_when_all_sources_empty():
    fx = _fx(client="", context="", env={})
    spec = {"from": "env.MISSING", "default": "fallback-default"}
    assert _resolve_ref(fx, spec) == "fallback-default"


def test_resolve_ref_empty_when_no_source():
    assert _resolve_ref(_fx(), {}) == ""


# --- _assemble_cli_args: args_template ----------------------------------


def test_assemble_positional_from_context():
    fx = _fx(context="https://example.com")
    src = {
        "command": ["freddy", "scrape"],
        "args_template": [{"kind": "positional", "from": "context"}],
        "arg_for_cache_key": {"from": "context"},
    }
    args, cache_key = _assemble_cli_args(fx, src)
    assert args == ["https://example.com"]
    assert cache_key == "https://example.com"


def test_assemble_flag_visibility_uses_client_as_brand():
    """Regression: freddy visibility needs --brand <brand>, not positional."""
    fx = _fx(client="bmw", context="https://www.bmw.de/", env={"AUTORESEARCH_VISIBILITY_KEYWORDS": "ev,i4"})
    src = {
        "command": ["freddy", "visibility"],
        "args_template": [
            {"kind": "flag", "flag": "--brand", "from": "client"},
            {"kind": "flag", "flag": "--keywords", "from": "env.AUTORESEARCH_VISIBILITY_KEYWORDS", "default": ""},
        ],
        "arg_for_cache_key": {"from": "client"},
    }
    args, cache_key = _assemble_cli_args(fx, src)
    # Order matches template declaration.
    assert args == ["--brand", "bmw", "--keywords", "ev,i4"]
    # Cache key aligns with what visibility.py::try_read_cache uses (brand).
    assert cache_key == "bmw"


def test_assemble_flag_skipped_when_empty_and_no_default():
    """Optional --keywords flag with empty env + empty default → not emitted."""
    fx = _fx(client="bmw", env={})
    src = {
        "command": ["freddy", "visibility"],
        "args_template": [
            {"kind": "flag", "flag": "--brand", "from": "client"},
            {"kind": "flag", "flag": "--keywords", "from": "env.AUTORESEARCH_VISIBILITY_KEYWORDS", "default": ""},
        ],
        "arg_for_cache_key": {"from": "client"},
    }
    args, _ = _assemble_cli_args(fx, src)
    assert args == ["--brand", "bmw"]
    assert "--keywords" not in args


def test_assemble_search_content_platform_flag_plus_positional_query():
    """freddy search-content --platform <p> <query>. platform from context, query from client."""
    fx = _fx(client="MrBeast", context="youtube")
    src = {
        "command": ["freddy", "search-content"],
        "args_template": [
            {"kind": "flag", "flag": "--platform", "from": "context"},
            {"kind": "positional", "from": "client"},
        ],
        "arg_for_cache_key": {"from": "client"},
    }
    args, cache_key = _assemble_cli_args(fx, src)
    assert args == ["--platform", "youtube", "MrBeast"]
    assert cache_key == "MrBeast"


def test_assemble_search_ads_domain_from_env_with_fallback_to_context():
    """search-ads wants a real domain; env override beats context slug."""
    fx_with_env = _fx(client="figma", context="figma", env={"AUTORESEARCH_SEARCH_ADS_DOMAIN": "figma.com"})
    fx_without_env = _fx(client="canva", context="canva.com")
    src = {
        "command": ["freddy", "search-ads"],
        "args_template": [{"kind": "positional", "from": "env.AUTORESEARCH_SEARCH_ADS_DOMAIN", "fallback_from": "context"}],
        "arg_for_cache_key": {"from": "env.AUTORESEARCH_SEARCH_ADS_DOMAIN", "fallback_from": "context"},
    }
    args, cache_key = _assemble_cli_args(fx_with_env, src)
    assert args == ["figma.com"]
    assert cache_key == "figma.com"

    args, cache_key = _assemble_cli_args(fx_without_env, src)
    assert args == ["canva.com"]
    assert cache_key == "canva.com"


def test_assemble_unknown_kind_raises():
    fx = _fx()
    src = {
        "command": ["freddy", "something"],
        "args_template": [{"kind": "weird-kind", "from": "context"}],
        "arg_for_cache_key": {"from": "context"},
    }
    with pytest.raises(ValueError, match="unknown args_template kind"):
        _assemble_cli_args(fx, src)


def test_assemble_flag_without_flag_key_raises():
    fx = _fx()
    src = {
        "command": ["freddy", "something"],
        "args_template": [{"kind": "flag", "from": "context"}],  # missing "flag"
        "arg_for_cache_key": {"from": "context"},
    }
    with pytest.raises(ValueError, match="missing 'flag'"):
        _assemble_cli_args(fx, src)


def test_assemble_missing_args_template_raises():
    """Descriptor without args_template is a config bug."""
    fx = _fx()
    src = {"command": ["freddy", "x"], "arg_for_cache_key": {"from": "context"}}
    with pytest.raises(ValueError, match="missing args_template or arg_for_cache_key"):
        _assemble_cli_args(fx, src)


def test_assemble_missing_arg_for_cache_key_raises():
    """Descriptor without arg_for_cache_key is a config bug."""
    fx = _fx()
    src = {
        "command": ["freddy", "x"],
        "args_template": [{"kind": "positional", "from": "context"}],
    }
    with pytest.raises(ValueError, match="missing args_template or arg_for_cache_key"):
        _assemble_cli_args(fx, src)


# --- sources.json shipped config -----------------------------------------


def test_shipped_sources_json_has_args_template_everywhere():
    """Every source descriptor must carry args_template + arg_for_cache_key."""
    config = _load_sources_config()
    for domain, descriptors in config["domains"].items():
        for desc in descriptors:
            assert "args_template" in desc, f"{domain}/{desc['source']} missing args_template"
            assert "arg_for_cache_key" in desc, f"{domain}/{desc['source']} missing arg_for_cache_key"


def test_shipped_geo_visibility_signature():
    """Visibility descriptor must use --brand <client> + --keywords flag."""
    config = _load_sources_config()
    vis = next(d for d in config["domains"]["geo"] if d["source"] == "freddy-visibility")
    kinds = [(e["kind"], e.get("flag"), e.get("from")) for e in vis["args_template"]]
    assert ("flag", "--brand", "client") in kinds
    assert any(f == "--keywords" for _, f, _ in kinds)


def test_shipped_storyboard_search_content_signature():
    """search-content descriptor must use --platform flag + positional query."""
    config = _load_sources_config()
    sc = next(d for d in config["domains"]["storyboard"] if d["source"] == "ic")
    kinds = [(e["kind"], e.get("flag"), e.get("from")) for e in sc["args_template"]]
    assert ("flag", "--platform", "context") in kinds
    assert ("positional", None, "client") in kinds
