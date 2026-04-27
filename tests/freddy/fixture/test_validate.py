import json

from typer.testing import CliRunner

from cli.freddy.commands.fixture import app as fixture_app


def _write(tmp_path, payload):
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(payload))
    return str(p)


def test_validate_accepts_well_formed_manifest(manifest_file):
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["validate", manifest_file()])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["fixtures"] == 1


def test_validate_rejects_missing_suite_version(tmp_path):
    path = _write(tmp_path, {
        "suite_id": "test-v1",
        "domains": {"geo": [{"fixture_id": "x", "client": "y",
                             "context": "z", "version": "1.0"}]},
    })
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["validate", path])
    assert result.exit_code != 0
    assert "version" in result.output.lower()


def test_validate_rejects_duplicate_fixture_ids(manifest_file):
    path = manifest_file(fixtures=[
        {"fixture_id": "dup", "client": "a", "context": "b", "version": "1.0"},
        {"fixture_id": "dup", "client": "c", "context": "d", "version": "1.0"},
    ])
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["validate", path])
    assert result.exit_code != 0
    assert "duplicate" in result.output.lower()


def test_validate_rejects_malformed_json(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not json")
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["validate", str(path)])
    assert result.exit_code != 0
    assert "json" in result.output.lower()
