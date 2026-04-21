"""Deterministically export FastAPI OpenAPI schema for frontend contract generation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

# Required defaults so app imports/openapi generation works in CI without secrets.
_DEFAULT_ENV = {
    "ENVIRONMENT": "development",
    "SUPABASE_URL": "http://localhost:54321",
    "SUPABASE_ANON_KEY": "test-anon-key",
    "SUPABASE_JWT_SECRET": "test-secret-key-for-ci-only-32characters",
    "GEMINI_API_KEY": "test-key",
    "R2_ACCOUNT_ID": "0123456789abcdef0123456789abcdef",
    "R2_ACCESS_KEY_ID": "test_access_key",
    "R2_SECRET_ACCESS_KEY": "test_secret_access_key",
    "R2_BUCKET_NAME": "test_bucket",
    "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
}


def _ensure_env_defaults() -> None:
    for key, value in _DEFAULT_ENV.items():
        os.environ.setdefault(key, value)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path override for exported OpenAPI JSON.",
    )
    return parser.parse_args()


def _resolve_output_path(root: Path, output_arg: Path | None) -> Path:
    output_env = os.environ.get("OPENAPI_OUTPUT_PATH")

    if output_arg is not None:
        output = output_arg
    elif output_env:
        output = Path(output_env)
    else:
        output = root / "frontend" / "src" / "lib" / "generated" / "openapi.json"

    if not output.is_absolute():
        return (root / output).resolve()
    return output


def main() -> None:
    args = _parse_args()
    _ensure_env_defaults()

    from src.api.main import app

    root = Path(__file__).resolve().parents[1]
    output_path = _resolve_output_path(root, args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    spec = app.openapi()

    serialized = json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=True)
    output_path.write_text(f"{serialized}\n", encoding="utf-8")

    print(output_path)


if __name__ == "__main__":
    main()
