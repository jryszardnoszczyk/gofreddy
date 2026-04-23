import json

from typer.testing import CliRunner

from cli.freddy.commands.fixture import app as fixture_app


def _manifest(tmp_path):
    payload = {
        "suite_id": "t-v1", "version": "1.0",
        "domains": {
            "geo": [{"fixture_id": "geo-a", "client": "x",
                     "context": "https://a.com", "version": "1.0", "anchor": True}],
            "monitoring": [{"fixture_id": "mon-a", "client": "b",
                            "context": "${SHOP_CONTEXT}", "version": "1.0",
                            "env": {"AUTORESEARCH_WEEK_RELATIVE": "most_recent_complete"}}],
        },
    }
    p = tmp_path / "m.json"
    p.write_text(json.dumps(payload))
    return str(p)


def test_list_prints_all_fixtures(tmp_path):
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["list", _manifest(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "geo-a" in result.output
    assert "mon-a" in result.output


def test_list_filters_by_domain(tmp_path):
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["list", _manifest(tmp_path), "--domain", "geo"])
    assert result.exit_code == 0
    assert "geo-a" in result.output
    assert "mon-a" not in result.output


def test_envs_lists_all_referenced_vars(tmp_path):
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["envs", _manifest(tmp_path)])
    assert result.exit_code == 0
    assert "SHOP_CONTEXT" in result.output


def test_envs_missing_flag_hides_set_vars(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOP_CONTEXT", "some-value")
    runner = CliRunner()
    result = runner.invoke(fixture_app, ["envs", _manifest(tmp_path), "--missing"])
    assert result.exit_code == 0
    assert "SHOP_CONTEXT" not in result.output
