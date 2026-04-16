"""Unit tests for domain rank snapshot parsing."""

from datetime import date

import pytest

from src.seo.providers.dataforseo import DataForSeoProvider
from src.seo.models import DomainRankSnapshot


class TestParseDomainRank:
    """Tests for DataForSeoProvider._parse_domain_rank()."""

    def test_parses_valid_response(self):
        raw = {
            "tasks": [
                {
                    "result": [
                        {
                            "rank": 150,
                            "backlinks": 5000,
                            "referring_domains": 200,
                        }
                    ]
                }
            ]
        }
        result = DataForSeoProvider._parse_domain_rank("example.com", raw)
        assert isinstance(result, DomainRankSnapshot)
        assert result.domain == "example.com"
        assert result.rank == 150
        assert result.backlinks_total == 5000
        assert result.referring_domains == 200
        assert result.snapshot_date == date.today()

    def test_empty_tasks(self):
        raw = {"tasks": []}
        result = DataForSeoProvider._parse_domain_rank("example.com", raw)
        assert result.domain == "example.com"
        assert result.rank is None
        assert result.snapshot_date == date.today()

    def test_null_result(self):
        raw = {"tasks": [{"result": None}]}
        result = DataForSeoProvider._parse_domain_rank("example.com", raw)
        assert result.domain == "example.com"
        assert result.rank is None

    def test_empty_result_list(self):
        raw = {"tasks": [{"result": []}]}
        result = DataForSeoProvider._parse_domain_rank("example.com", raw)
        assert result.domain == "example.com"

    def test_missing_fields_default_to_zero(self):
        raw = {"tasks": [{"result": [{"rank": 50}]}]}
        result = DataForSeoProvider._parse_domain_rank("example.com", raw)
        assert result.rank == 50
        assert result.backlinks_total == 0
        assert result.referring_domains == 0

    def test_null_values_default_to_zero(self):
        raw = {"tasks": [{"result": [{"rank": 50, "backlinks": None, "referring_domains": None}]}]}
        result = DataForSeoProvider._parse_domain_rank("example.com", raw)
        assert result.backlinks_total == 0
        assert result.referring_domains == 0
