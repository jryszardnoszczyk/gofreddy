"""Shared enums for the video intelligence platform."""

from enum import Enum


class Platform(str, Enum):
    """Supported video platforms."""

    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TWITCH = "twitch"
    TWITTER = "twitter"
    ONLYFANS = "onlyfans"
