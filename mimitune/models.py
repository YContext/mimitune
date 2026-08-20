"""
Data models for YouTube Music (InnerTube API) objects.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class YouTubeLocale:
    gl: str = "US"
    hl: str = "en"


@dataclass
class PlaybackAuthState:
    visitor_data: Optional[str] = None
    data_sync_id: Optional[str] = None
    cookie: Optional[str] = None
    po_token: Optional[str] = None

    @property
    def has_login_cookie(self) -> bool:
        if not self.cookie:
            return False
        return "SAPISID" in self.cookie or "__Secure-3PAPISID" in self.cookie


@dataclass
class YouTubeClientPreset:
    client_name: str
    client_version: str
    client_id: str
    user_agent: str
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    device_make: Optional[str] = None
    device_model: Optional[str] = None
    android_sdk_version: Optional[str] = None
    build_id: Optional[str] = None
    cronet_version: Optional[str] = None
    package_name: Optional[str] = None
    friendly_name: Optional[str] = None
    login_supported: bool = False
    login_required: bool = False
    use_signature_timestamp: bool = False
    is_embedded: bool = False

    def request_origin(self) -> str:
        name = self.client_name.upper()
        if name in ("TVHTML5", "TVHTML5_SIMPLY_EMBEDDED_PLAYER", "TVHTML5_SIMPLY"):
            return "https://www.youtube.com"
        return "https://music.youtube.com"

    def request_referer(self) -> str:
        name = self.client_name.upper()
        if name in ("TVHTML5", "TVHTML5_SIMPLY_EMBEDDED_PLAYER", "TVHTML5_SIMPLY"):
            return "https://www.youtube.com/tv"
        return "https://music.youtube.com/"


# Client Presets
USER_AGENT_WEB = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)

WEB = YouTubeClientPreset(
    client_name="WEB",
    client_version="2.20260114.00.00",
    client_id="1",
    user_agent=USER_AGENT_WEB,
)

WEB_REMIX = YouTubeClientPreset(
    client_name="WEB_REMIX",
    client_version="1.20260114.01.00",
    client_id="67",
    user_agent=USER_AGENT_WEB,
    login_supported=True,
    use_signature_timestamp=True,
)

ANDROID_MUSIC = YouTubeClientPreset(
    client_name="ANDROID_MUSIC",
    client_version="7.27.52",
    client_id="21",
    user_agent="com.google.android.apps.youtube.music/7.27.52 (Linux; U; Android 15; en_US; Pixel 9 Pro; Build/AP4A.250205.002; Cronet/132.0.6834.79) gzip",
    os_name="Android",
    os_version="15",
    device_make="Google",
    device_model="Pixel 9 Pro",
    android_sdk_version="35",
    login_supported=True,
    use_signature_timestamp=True,
)

TVHTML5 = YouTubeClientPreset(
    client_name="TVHTML5",
    client_version="7.20260114.00.00",
    client_id="7",
    user_agent="Mozilla/5.0(SMART-TV; Linux; Tizen 4.0.0.2) AppleWebkit/605.1.15 (KHTML, like Gecko) SamsungBrowser/9.2 TV Safari/605.1.15",
    login_supported=True,
    login_required=True,
    use_signature_timestamp=True,
)


@dataclass
class Artist:
    name: str
    id: Optional[str] = None


@dataclass
class SongItem:
    id: str
    title: str
    artists: List[Artist] = field(default_factory=list)
    duration: Optional[str] = None
    thumbnail: Optional[str] = None
    explicit: bool = False
    album: Optional[str] = None
    set_video_id: Optional[str] = None
    chart_position: Optional[int] = None
    chart_change: Optional[str] = None


@dataclass
class AlbumItem:
    browse_id: str
    playlist_id: str
    title: str
    artists: List[Artist] = field(default_factory=list)
    year: Optional[int] = None
    thumbnail: Optional[str] = None
    explicit: bool = False


@dataclass
class ArtistItem:
    id: str
    title: str
    thumbnail: Optional[str] = None
    channel_id: Optional[str] = None
    subscriber_count_text: Optional[str] = None
    monthly_listener_count_text: Optional[str] = None


@dataclass
class PlaylistItem:
    id: str
    title: str
    author: Optional[Artist] = None
    song_count_text: Optional[str] = None
    thumbnail: Optional[str] = None
    description: Optional[str] = None
    is_editable: bool = False


@dataclass
class SearchSummary:
    title: str
    items: List[Any] = field(default_factory=list)


@dataclass
class SearchSummaryPage:
    summaries: List[SearchSummary] = field(default_factory=list)


@dataclass
class SearchResult:
    items: List[Any] = field(default_factory=list)
    continuation: Optional[str] = None


@dataclass
class AlbumPage:
    album: AlbumItem
    songs: List[SongItem] = field(default_factory=list)
    other_versions: List[AlbumItem] = field(default_factory=list)


@dataclass
class ArtistSection:
    title: str
    items: List[Any] = field(default_factory=list)


@dataclass
class ArtistPage:
    artist: ArtistItem
    sections: List[ArtistSection] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class ArtistItemsPage:
    title: str
    items: List[Any] = field(default_factory=list)
    continuation: Optional[str] = None


@dataclass
class PlaylistPage:
    playlist: PlaylistItem
    songs: List[SongItem] = field(default_factory=list)
    songs_continuation: Optional[str] = None
    continuation: Optional[str] = None


@dataclass
class HomeSection:
    title: str
    items: List[Any] = field(default_factory=list)


@dataclass
class HomePage:
    chips: List[Dict[str, str]] = field(default_factory=list)
    sections: List[HomeSection] = field(default_factory=list)
    continuation: Optional[str] = None


@dataclass
class ExplorePage:
    new_release_albums: List[AlbumItem] = field(default_factory=list)
    mood_and_genres: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ChartSection:
    title: str
    items: List[Any] = field(default_factory=list)
    chart_type: str = "GENRE"


@dataclass
class ChartsPage:
    sections: List[ChartSection] = field(default_factory=list)
    continuation: Optional[str] = None


@dataclass
class LibraryPage:
    items: List[Any] = field(default_factory=list)
    continuation: Optional[str] = None


@dataclass
class HistorySection:
    title: str
    items: List[SongItem] = field(default_factory=list)


@dataclass
class HistoryPage:
    sections: List[HistorySection] = field(default_factory=list)


@dataclass
class AccountInfo:
    name: Optional[str] = None
    handle: Optional[str] = None
    email: Optional[str] = None
    channel_id: Optional[str] = None


@dataclass
class MediaInfo:
    video_id: str
    title: Optional[str] = None
    author: Optional[str] = None
    author_id: Optional[str] = None
    author_thumbnail: Optional[str] = None
    description: Optional[str] = None
    subscribers: Optional[str] = None
    upload_date: Optional[str] = None
    view_count: Optional[int] = None
    like: Optional[int] = None
    dislike: Optional[int] = None


@dataclass
class TranscriptCue:
    time_ms: int
    text: str


@dataclass
class NextResult:
    title: Optional[str] = None
    items: List[SongItem] = field(default_factory=list)
    current_index: Optional[int] = None
    lyrics_browse_id: Optional[str] = None
    related_browse_id: Optional[str] = None
    continuation: Optional[str] = None


@dataclass
class PlayerResponse:
    playability_status: Dict[str, Any] = field(default_factory=dict)
    streaming_data: Dict[str, Any] = field(default_factory=dict)
    video_details: Dict[str, Any] = field(default_factory=dict)
    raw_response: Dict[str, Any] = field(default_factory=dict)
