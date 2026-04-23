"""HTTP security + privacy header inspection.

Not explicitly numbered in `data/preflight_lenses.yaml` (most preflight lenses
are well-known files); this check backstops the headers-based signals Stage-2
agents need without an LLM call.

Expected signal shape (homepage + /pricing + /about sampled):

    {
        "pages_sampled": [str],
        "strict_transport_security": {"present": bool, "max_age": int | None, "preload": bool},
        "content_security_policy":   {"present": bool, "report_only": bool, "directives": [str]},
        "x_frame_options":           {"present": bool, "value": str | None},
        "referrer_policy":           {"present": bool, "value": str | None},
        "permissions_policy":        {"present": bool, "features_restricted": [str]},
        "coop":                      {"present": bool, "value": str | None},
        "coep":                      {"present": bool, "value": str | None},
    }

Implementation note (v1): httpx HEAD requests (fall back to GET if HEAD 405).
No auth — headers are public. Don't evaluate strictness here; just capture
the values. Stage-2 agents interpret.
"""
from __future__ import annotations


async def check(domain: str) -> dict:
    # TODO(v1-step-C): implement via httpx HEAD → GET fallback.
    return {"implemented": False}
