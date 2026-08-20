"""
OpenTune YouTube Music API Python Package.
Reverse-engineered from OpenTune Android App (InnerTube API).
"""

from opentune_ytmusic.models import (
    YouTubeLocale,
    PlaybackAuthState,
    YouTubeClientPreset,
    WEB,
    WEB_REMIX,
    ANDROID_MUSIC,
    TVHTML5,
    Artist,
    SongItem,
    AlbumItem,
    ArtistItem,
    PlaylistItem,
    SearchSummary,
    SearchSummaryPage,
    SearchResult,
    AlbumPage,
    ArtistPage,
    PlaylistPage,
    HomePage,
    ExplorePage,
    ChartsPage,
    AccountInfo,
    MediaInfo,
    NextResult,
    PlayerResponse,
)
from opentune_ytmusic.client import InnerTubeClient
from opentune_ytmusic.api import YTMusic

__all__ = [
    "YouTubeLocale",
    "PlaybackAuthState",
    "YouTubeClientPreset",
    "WEB",
    "WEB_REMIX",
    "ANDROID_MUSIC",
    "TVHTML5",
    "Artist",
    "SongItem",
    "AlbumItem",
    "ArtistItem",
    "PlaylistItem",
    "SearchSummary",
    "SearchSummaryPage",
    "SearchResult",
    "AlbumPage",
    "ArtistPage",
    "PlaylistPage",
    "HomePage",
    "ExplorePage",
    "ChartsPage",
    "AccountInfo",
    "MediaInfo",
    "NextResult",
    "PlayerResponse",
    "InnerTubeClient",
    "YTMusic",
]

__version__ = "0.1.0"
