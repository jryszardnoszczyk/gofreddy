from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPORT_SCRIPT = PROJECT_ROOT / "scripts" / "export_openapi.py"


def run_export(output_path: Path) -> bytes:
    env = os.environ.copy()
    env.update(
        {
            "ENVIRONMENT": "development",
            "SUPABASE_URL": "http://localhost:54321",
            "SUPABASE_ANON_KEY": "test-anon-key",
            "SUPABASE_JWT_SECRET": "test-secret-key-for-ci-only-32characters",
            "GEMINI_API_KEY": "AIzaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "R2_ACCOUNT_ID": "0123456789abcdef0123456789abcdef",
            "R2_ACCESS_KEY_ID": "test_access_key",
            "R2_SECRET_ACCESS_KEY": "test_secret_access_key",
            "R2_BUCKET_NAME": "test_bucket",
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        }
    )

    subprocess.run(
        ["uv", "run", "python", str(EXPORT_SCRIPT), "--output", str(output_path)],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return output_path.read_bytes()


def test_export_openapi_is_deterministic_and_well_formed(tmp_path: Path) -> None:
    output_path = tmp_path / "openapi.json"

    first = run_export(output_path)
    second = run_export(output_path)

    assert first == second

    spec = json.loads(first)
    assert isinstance(spec.get("paths"), dict)

    components = spec.get("components")
    assert isinstance(components, dict)
    schemas = components.get("schemas")
    assert isinstance(schemas, dict)

    video_result_schema = schemas.get("VideoAnalysisResult")
    assert isinstance(video_result_schema, dict)
    assert "overall_confidence" in video_result_schema.get("required", [])

    risks_schema = schemas.get("RiskDetectionResponse")
    assert isinstance(risks_schema, dict)
    assert set(risks_schema.get("required", [])) >= {
        "risk_type",
        "category",
        "severity",
        "confidence",
        "description",
        "evidence",
    }
    risk_props = risks_schema.get("properties", {})
    assert isinstance(risk_props, dict)
    category_prop = risk_props.get("category")
    assert isinstance(category_prop, dict)
    assert category_prop.get("deprecated") is True

    risks_detected = video_result_schema.get("properties", {}).get("risks_detected")
    assert isinstance(risks_detected, dict)
    items = risks_detected.get("items")
    assert isinstance(items, dict)
    assert items.get("$ref") == "#/components/schemas/RiskDetectionResponse"
