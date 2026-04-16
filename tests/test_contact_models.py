"""Tests for CRM contact models."""

from datetime import datetime, timezone
from uuid import uuid4

from src.monitoring.crm.models import Contact


class TestContactFromRow:
    def test_from_row_parses_list_handles(self):
        row = {
            "id": uuid4(), "org_id": uuid4(),
            "primary_handle": "@user", "primary_platform": "twitter",
            "display_name": "User", "avatar_url": None,
            "handles": [{"platform": "twitter", "handle": "@user"}],
            "interaction_count": 5,
            "first_seen_at": datetime.now(timezone.utc),
            "last_seen_at": datetime.now(timezone.utc),
            "notes": None, "tags": ["influencer", "vip"],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        contact = Contact.from_row(row)
        assert contact.primary_handle == "@user"
        assert contact.handles == [{"platform": "twitter", "handle": "@user"}]
        assert contact.tags == ["influencer", "vip"]
        assert contact.interaction_count == 5

    def test_from_row_handles_string_json(self):
        row = {
            "id": uuid4(), "org_id": uuid4(),
            "primary_handle": "user", "primary_platform": "instagram",
            "display_name": None, "avatar_url": None,
            "handles": '[]', "interaction_count": 0,
            "first_seen_at": datetime.now(timezone.utc),
            "last_seen_at": datetime.now(timezone.utc),
            "notes": None, "tags": '["tag1"]',
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        contact = Contact.from_row(row)
        assert contact.handles == []
        assert contact.tags == ["tag1"]
        assert contact.display_name is None

    def test_from_row_handles_none_handles_and_tags(self):
        row = {
            "id": uuid4(), "org_id": uuid4(),
            "primary_handle": "u", "primary_platform": "tiktok",
            "display_name": "TikToker", "avatar_url": "https://img.com/a.png",
            "handles": None, "interaction_count": 1,
            "first_seen_at": datetime.now(timezone.utc),
            "last_seen_at": datetime.now(timezone.utc),
            "notes": "Some notes", "tags": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        contact = Contact.from_row(row)
        assert contact.handles == []
        assert contact.tags == []
        assert contact.notes == "Some notes"
        assert contact.avatar_url == "https://img.com/a.png"

    def test_from_row_string_json_with_multiple_handles(self):
        handles_json = '[{"platform": "twitter", "handle": "@a"}, {"platform": "instagram", "handle": "b"}]'
        row = {
            "id": uuid4(), "org_id": uuid4(),
            "primary_handle": "@a", "primary_platform": "twitter",
            "display_name": "A", "avatar_url": None,
            "handles": handles_json, "interaction_count": 3,
            "first_seen_at": datetime.now(timezone.utc),
            "last_seen_at": datetime.now(timezone.utc),
            "notes": None, "tags": '[]',
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        contact = Contact.from_row(row)
        assert len(contact.handles) == 2
        assert contact.handles[0]["platform"] == "twitter"
        assert contact.handles[1]["handle"] == "b"
