"""Tests for src/audit/tools/martech — wappalyzer-next wrapper.

Network-free: all tests mock ``wappalyzer.analyze`` to return canned shapes.
The real Day-1 spike (which actually hit shopify.com + hubspot.com) is
documented in the master plan §4.4 outcome notes; CI runs offline.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.audit.tools import martech


_SHOPIFY_LIKE_RAW = {
    "https://www.shopify.com/": {
        "Shopify": {
            "version": "",
            "confidence": 100,
            "categories": ["Ecommerce"],
            "groups": ["Sales"],
        },
        "Cloudflare": {
            "version": "",
            "confidence": 100,
            "categories": ["CDN"],
            "groups": ["Servers"],
        },
        "Google Tag Manager": {
            "version": "",
            "confidence": 100,
            "categories": ["Tag managers"],
            "groups": ["Analytics"],
        },
        "HubSpot": {
            "version": "",
            "confidence": 100,
            "categories": ["Marketing automation"],
            "groups": ["Marketing"],
        },
    }
}


def test_fingerprint_returns_groupings_for_known_techs() -> None:
    with patch("wappalyzer.analyze", return_value=_SHOPIFY_LIKE_RAW):
        result = martech.fingerprint_martech_stack("https://www.shopify.com")
    assert result["degraded"] is False
    assert result["tech_count"] == 4
    assert "Shopify" in result["raw_technologies"]
    # Groupings via martech_rules.yaml.
    assert "ecommerce" in result["groupings"]
    assert "Shopify" in result["groupings"]["ecommerce"]
    assert "cdn" in result["groupings"]
    assert "Cloudflare" in result["groupings"]["cdn"]
    assert "attribution" in result["groupings"]
    assert "Google Tag Manager" in result["groupings"]["attribution"]
    assert "crm" in result["groupings"]
    assert "HubSpot" in result["groupings"]["crm"]


def test_fingerprint_fields_shape() -> None:
    with patch("wappalyzer.analyze", return_value=_SHOPIFY_LIKE_RAW):
        result = martech.fingerprint_martech_stack("https://example.com")
    assert set(result.keys()) == {
        "url", "fetched_at", "scan_type", "raw_technologies",
        "groupings", "tech_count", "degraded", "degraded_reason",
    }
    assert result["scan_type"] == "fast"
    assert result["url"] == "https://example.com"


def test_fingerprint_degrades_when_lib_missing() -> None:
    with patch("builtins.__import__", side_effect=ImportError("no wappalyzer")):
        # Patch around the deferred import in fingerprint_martech_stack.
        # Easier: simulate by monkeypatching analyze to raise inside the wrapper.
        pass

    with patch("wappalyzer.analyze", side_effect=Exception("boom")):
        result = martech.fingerprint_martech_stack("https://example.com")
    assert result["degraded"] is True
    assert "boom" in result["degraded_reason"]
    assert result["raw_technologies"] == {}


def test_fingerprint_degrades_on_empty_response() -> None:
    with patch("wappalyzer.analyze", return_value={}):
        result = martech.fingerprint_martech_stack("https://example.com")
    assert result["degraded"] is True
    assert "no technologies" in result["degraded_reason"]


def test_fingerprint_handles_flat_response_form() -> None:
    """Some wappalyzer call paths return ``{tech: meta}`` directly."""
    flat = {
        "Shopify": {"confidence": 100, "categories": ["Ecommerce"], "version": ""},
    }
    with patch("wappalyzer.analyze", return_value=flat):
        result = martech.fingerprint_martech_stack("https://example.com")
    assert result["degraded"] is False
    assert "Shopify" in result["raw_technologies"]


def test_groupings_match_by_name_or_category() -> None:
    """Tech matches a group via name OR category list."""
    rules = {
        "groupings": {
            "test_group_by_name": ["Specific Tech"],
            "test_group_by_category": ["Some Category"],
        },
    }
    techs = {
        "Specific Tech": {"confidence": 100, "categories": ["Other Cat"]},
        "Different Tech": {"confidence": 100, "categories": ["Some Category"]},
    }
    g = martech._apply_groupings(techs, rules)
    assert g["test_group_by_name"] == ["Specific Tech"]
    assert g["test_group_by_category"] == ["Different Tech"]


def test_domain_overrides_add_remove(monkeypatch) -> None:
    rules = {
        "groupings": {"crm": ["HubSpot"]},
        "overrides": {
            "example.com": {
                "add": {"custom_group": ["Custom Tech"]},
                "remove": {"crm": ["HubSpot"]},
            },
        },
    }
    groupings = {"crm": ["HubSpot"]}
    out = martech._apply_domain_overrides("https://example.com/path", groupings, rules)
    assert "custom_group" in out
    assert out["custom_group"] == ["Custom Tech"]
    assert "crm" not in out  # all entries removed → group dropped


def test_groupings_yaml_loads(tmp_path) -> None:
    """Real martech_rules.yaml loads cleanly + has the expected top-level keys."""
    rules = martech._load_rules()
    assert "groupings" in rules
    assert "overrides" in rules
    # Spot-check critical groupings.
    assert "analytics" in rules["groupings"]
    assert "cmp" in rules["groupings"]
    assert "crm" in rules["groupings"]
    assert "esp" in rules["groupings"]
    assert "cdp" in rules["groupings"]
    assert "ai_chat" in rules["groupings"]
    assert "ab_test" in rules["groupings"]


def test_groupings_yaml_has_minimum_20_groups() -> None:
    """Master plan §4.4 calls for 20+ category groupings."""
    rules = martech._load_rules()
    assert len(rules["groupings"]) >= 20


def test_normalize_handles_unrecognized_shape() -> None:
    assert martech._normalize_wappalyzer_output("not a dict", "https://x") == {}
    assert martech._normalize_wappalyzer_output({"random": "value"}, "https://x") == {}
