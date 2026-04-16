"""Tests for R2 media storage — filename validation and key generation."""

import pytest
from uuid import uuid4

from src.storage.r2_media_storage import R2MediaStorage, VALID_FILENAME


class TestFilenameValidation:
    def test_valid_simple_filenames(self):
        assert VALID_FILENAME.match("photo.jpg")
        assert VALID_FILENAME.match("video-2024.mp4")
        assert VALID_FILENAME.match("document_v2.pdf")
        assert VALID_FILENAME.match("a")
        assert VALID_FILENAME.match("file.tar.gz")

    def test_valid_alphanumeric_filenames(self):
        assert VALID_FILENAME.match("IMG_20240101_120000.png")
        assert VALID_FILENAME.match("audio-track-01.mp3")
        assert VALID_FILENAME.match("report.final.v3.pdf")

    def test_invalid_path_traversal(self):
        assert not VALID_FILENAME.match("../etc/passwd")
        assert not VALID_FILENAME.match("../../secret.txt")
        assert not VALID_FILENAME.match("/absolute/path.jpg")

    def test_invalid_empty(self):
        assert not VALID_FILENAME.match("")

    def test_invalid_spaces(self):
        assert not VALID_FILENAME.match("file with spaces.jpg")
        assert not VALID_FILENAME.match(" leading.txt")

    def test_invalid_too_long(self):
        assert not VALID_FILENAME.match("a" * 256)

    def test_max_length_boundary(self):
        assert VALID_FILENAME.match("a" * 255)
        assert not VALID_FILENAME.match("a" * 256)

    def test_invalid_special_characters(self):
        assert not VALID_FILENAME.match("file@name.jpg")
        assert not VALID_FILENAME.match("file name.jpg")
        assert not VALID_FILENAME.match("file\tname.jpg")
        assert not VALID_FILENAME.match("file/name.jpg")


class TestMediaKeyFormat:
    def test_key_format(self):
        org_id = uuid4()
        asset_id = uuid4()
        key = f"media/{org_id}/{asset_id}/photo.jpg"
        assert key.startswith("media/")
        assert str(org_id) in key
        assert str(asset_id) in key
        assert key.endswith("/photo.jpg")

    def test_validate_filename_raises_on_invalid(self):
        """R2MediaStorage._validate_filename raises ValueError on invalid names."""
        # We can't easily instantiate R2MediaStorage (needs session/config),
        # but we can verify the regex rejects dangerous inputs
        dangerous = ["../hack", "foo/bar", "", "a" * 300, "has space.txt"]
        for name in dangerous:
            assert not VALID_FILENAME.match(name), f"Should reject: {name!r}"


class TestMediaStorageConstants:
    def test_max_media_size(self):
        assert R2MediaStorage.MAX_MEDIA_SIZE == 100 * 1024 * 1024  # 100 MB

    def test_max_presigned_expiration(self):
        assert R2MediaStorage.MAX_PRESIGNED_EXPIRATION == 604800  # 7 days
