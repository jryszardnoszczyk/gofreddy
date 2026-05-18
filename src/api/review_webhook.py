"""FastAPI router for pre-publish review approve/reject URL clicks (U7).

Per the plan-level Threat Model + D14: approve/reject URLs land on a
confirmation page (safe GET); the actual state mutation is a POST with
a CSRF check. This blocks corporate-email-scanner / antivirus auto-fires
that would otherwise consume the token via a passive GET.

Single-use tokens enforced server-side by ReviewService.process_decision
(nonce table); tampering rejected by HMAC verify; expiry by token TTL.

Wire this router into the main FastAPI app via:

    from src.api.review_webhook import router as review_router
    app.include_router(review_router)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from src.review.service import (
    ALLOWED_DECISIONS,
    InvalidTokenError,
    ReviewService,
    TokenExpiredError,
    TokenReusedError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_service(request: Request) -> ReviewService:
    """Resolve the ReviewService from app state — operators install via
    `app.state.review_service = ReviewService(...)` at startup. Tests
    install a fixture-scoped instance pointed at tmp_path."""
    svc = getattr(request.app.state, "review_service", None)
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="review service not configured on this server",
        )
    return svc


def _confirmation_page_html(action: str, token: str) -> str:
    """Minimal CSRF defense: GET shows a form; POST executes.

    The CSRF mechanism is structural — corporate-email scanners and
    antivirus auto-fetchers issue GETs but never submit forms, so the
    state mutation only fires when a human clicks the form's submit
    button. No double-submit cookie is needed because the action is
    idempotent at the application level (single-use nonce).

    Per the 4-agent review (sec-1 T1-B): action + token are caller-
    controlled URL components; html.escape both before interpolation
    into the form action attribute.
    """
    import html as _html
    action_safe = _html.escape(action, quote=True)
    token_safe = _html.escape(token, quote=True)
    action_label = _html.escape(action.capitalize(), quote=True)
    return f"""<!DOCTYPE html>
<html>
<head><title>Confirm {action_label}</title></head>
<body style="font-family: system-ui, sans-serif; max-width: 600px; margin: 4rem auto; padding: 2rem;">
  <h1>Confirm {action_label}</h1>
  <p>You are about to <strong>{action_label.lower()}</strong> this artifact.</p>
  <form method="POST" action="/review/{action_safe}/{token_safe}">
    <p>
      <label>Reviewer note (recommended; required for rejection):<br>
        <textarea name="reviewer_note" rows="4" cols="60"></textarea>
      </label>
    </p>
    <p>
      <label>Reason (for rejection):<br>
        <input name="reason" type="text" size="60">
      </label>
    </p>
    <p>
      <label>Your email (for audit trail):<br>
        <input name="reviewer_email" type="email" size="60" required>
      </label>
    </p>
    <button type="submit">Confirm {action_label}</button>
  </form>
</body>
</html>"""


@router.get("/review/{action}/{token}", response_class=HTMLResponse)
async def review_confirmation_page(action: str, token: str) -> HTMLResponse:
    """GET: render confirmation form. State NOT mutated on this request."""
    if action not in ALLOWED_DECISIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"action must be one of {sorted(ALLOWED_DECISIONS)}",
        )
    return HTMLResponse(_confirmation_page_html(action, token))


@router.post("/review/{action}/{token}", response_class=HTMLResponse)
async def review_submit_decision(
    request: Request,
    action: str,
    token: str,
    reviewer_email: str = Form(...),
    reason: str = Form(""),
    reviewer_note: str = Form(""),
) -> HTMLResponse:
    """POST: execute the decision via ReviewService."""
    if action not in ALLOWED_DECISIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"action must be one of {sorted(ALLOWED_DECISIONS)}",
        )

    svc = _get_service(request)
    try:
        response = svc.process_decision(
            token, action,  # type: ignore[arg-type]
            reason=reason,
            reviewer_note=reviewer_note,
            reviewer_email=reviewer_email,
        )
    except InvalidTokenError as exc:
        logger.warning("review token rejected: %s", exc)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except TokenExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc))
    except TokenReusedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValueError as exc:
        # Hard-block guard + decision-token mismatch.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Per the 4-agent review (sec-1 T1-B): every interpolated value is
    # HTML-escaped so attacker-controllable artifact_id / client_slug
    # text cannot script in the reviewer's authenticated browser session.
    import html as _html
    decision_safe = _html.escape(response.decision.capitalize(), quote=True)
    artifact_id_safe = _html.escape(response.artifact_id, quote=True)
    client_slug_safe = _html.escape(response.client_slug, quote=True)
    return HTMLResponse(
        f"<!DOCTYPE html><html><body>"
        f"<h1>{decision_safe}d</h1>"
        f"<p>Artifact <code>{artifact_id_safe}</code> "
        f"({client_slug_safe}) — thank you.</p>"
        f"</body></html>"
    )


__all__ = ["router"]
