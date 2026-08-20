"""
High-level YouTube Music API wrapper for OpenTune YouTube Music Client.
"""

from typing import Optional, Dict, Any, List
import httpx

from opentune_ytmusic.models import (
    YouTubeLocale,
    PlaybackAuthState,
    YouTubeClientPreset,
    WEB,
    WEB_REMIX,
    SongItem,
    AlbumItem,
    ArtistItem,
    PlaylistItem,
    SearchSummaryPage,
    SearchResult,
    AlbumPage,
    PlaylistPage,
    ExplorePage,
    ChartsPage,
    ChartSection,
    AccountInfo,
    MediaInfo,
    NextResult,
    PlayerResponse,
)
from opentune_ytmusic.client import InnerTubeClient
from opentune_ytmusic.parsers import (
    parse_search_summary_response,
    parse_search_response,
    parse_album_response,
    parse_playlist_response,
    parse_account_menu_response,
    parse_next_response,
    extract_runs_text,
    extract_artist_runs,
    extract_thumbnail_url,
    parse_two_row_item,
    parse_responsive_list_item,
)


class YTMusic:
    def __init__(
        self,
        locale: Optional[YouTubeLocale] = None,
        auth_state: Optional[PlaybackAuthState] = None,
        cookie: Optional[str] = None,
        visitor_data: Optional[str] = None,
        po_token: Optional[str] = None,
        proxy: Optional[str] = None,
    ):
        if auth_state is None and (cookie or visitor_data or po_token):
            auth_state = PlaybackAuthState(
                cookie=cookie,
                visitor_data=visitor_data,
                po_token=po_token,
            )

        self.client = InnerTubeClient(
            locale=locale,
            auth_state=auth_state,
            default_client=WEB_REMIX,
            proxy=proxy,
        )

    def search_summary(self, query: str) -> SearchSummaryPage:
        response = self.client.search(query=query)
        return parse_search_summary_response(response)

    def search(
        self,
        query: str,
        filter_param: Optional[str] = None,
        continuation: Optional[str] = None,
    ) -> SearchResult:
        response = self.client.search(
            query=query,
            params=filter_param,
            continuation=continuation,
        )
        return parse_search_response(response)

    def get_album(self, browse_id: str) -> AlbumPage:
        response = self.client.browse(browse_id=browse_id)
        return parse_album_response(response, browse_id)

    def get_playlist(self, playlist_id: str) -> PlaylistPage:
        clean_id = playlist_id if playlist_id.startswith("VL") else f"VL{playlist_id}"
        response = self.client.browse(browse_id=clean_id, set_login=True)
        return parse_playlist_response(response, playlist_id)

    def get_explore(self) -> ExplorePage:
        response = self.client.browse(browse_id="FEmusic_explore")
        contents = (
            response.get("contents", {})
            .get("singleColumnBrowseResultsRenderer", {})
            .get("tabs", [{}])[0]
            .get("tabRenderer", {})
            .get("content", {})
            .get("sectionListRenderer", {})
            .get("contents", [])
        )

        albums = []
        genres = []

        for section in contents:
            carousel = section.get("musicCarouselShelfRenderer")
            if carousel:
                for item in carousel.get("contents", []):
                    two_row = item.get("musicTwoRowItemRenderer")
                    if two_row:
                        parsed = parse_two_row_item(two_row)
                        if isinstance(parsed, AlbumItem):
                            albums.append(parsed)

        return ExplorePage(new_release_albums=albums, mood_and_genres=genres)

    def get_charts(self) -> ChartsPage:
        response = self.client.browse(
            browse_id="FEmusic_charts",
            params="ggMGCgQIgAQ%3D",
        )
        sections = []
        contents = (
            response.get("contents", {})
            .get("singleColumnBrowseResultsRenderer", {})
            .get("tabs", [{}])[0]
            .get("tabRenderer", {})
            .get("content", {})
            .get("sectionListRenderer", {})
            .get("contents", [])
        )

        for content in contents:
            carousel = content.get("musicCarouselShelfRenderer")
            if carousel:
                title = extract_runs_text(
                    carousel.get("header", {})
                    .get("musicCarouselShelfBasicHeaderRenderer", {})
                    .get("title")
                ) or "Chart"
                items = []
                for item in carousel.get("contents", []):
                    parsed = parse_responsive_list_item(item) or (
                        parse_two_row_item(item.get("musicTwoRowItemRenderer"))
                        if item.get("musicTwoRowItemRenderer")
                        else None
                    )
                    if parsed:
                        items.append(parsed)
                if items:
                    sections.append(ChartSection(title=title, items=items))

        return ChartsPage(sections=sections)

    def get_player(
        self,
        video_id: str,
        playlist_id: Optional[str] = None,
        client_preset: YouTubeClientPreset = WEB_REMIX,
    ) -> PlayerResponse:
        response = self.client.player(
            video_id=video_id,
            playlist_id=playlist_id,
            client=client_preset,
        )
        return PlayerResponse(
            playability_status=response.get("playabilityStatus", {}),
            streaming_data=response.get("streamingData", {}),
            video_details=response.get("videoDetails", {}),
            raw_response=response,
        )

    def get_next(
        self,
        video_id: Optional[str] = None,
        playlist_id: Optional[str] = None,
        playlist_set_video_id: Optional[str] = None,
        index: Optional[int] = None,
        params: Optional[str] = None,
        continuation: Optional[str] = None,
    ) -> NextResult:
        response = self.client.next(
            video_id=video_id,
            playlist_id=playlist_id,
            playlist_set_video_id=playlist_set_video_id,
            index=index,
            params=params,
            continuation=continuation,
        )
        return parse_next_response(response)

    def get_lyrics(self, lyrics_browse_id: str) -> Optional[str]:
        response = self.client.browse(browse_id=lyrics_browse_id)
        contents = (
            response.get("contents", {})
            .get("sectionListRenderer", {})
            .get("contents", [{}])[0]
            .get("musicDescriptionShelfRenderer", {})
            .get("description")
        )
        return extract_runs_text(contents)

    def get_account_info(self) -> AccountInfo:
        response = self.client.account_menu()
        return parse_account_menu_response(response)

    def like_video(self, video_id: str, like: bool = True) -> Dict[str, Any]:
        return self.client.like_video(video_id=video_id, like=like)

    def like_playlist(self, playlist_id: str, like: bool = True) -> Dict[str, Any]:
        return self.client.like_playlist(playlist_id=playlist_id, like=like)

    def add_to_playlist(self, playlist_id: str, video_id: str) -> Dict[str, Any]:
        action = {"action": "ACTION_ADD_VIDEO", "addedVideoId": video_id}
        return self.client.edit_playlist(playlist_id=playlist_id, actions=[action])

    def remove_from_playlist(
        self, playlist_id: str, video_id: str, set_video_id: str
    ) -> Dict[str, Any]:
        action = {
            "action": "ACTION_REMOVE_VIDEO",
            "removedVideoId": video_id,
            "setVideoId": set_video_id,
        }
        return self.client.edit_playlist(playlist_id=playlist_id, actions=[action])

    def create_playlist(self, title: str) -> str:
        res = self.client.create_playlist(title=title)
        return res.get("playlistId", "")

    def delete_playlist(self, playlist_id: str) -> Dict[str, Any]:
        return self.client.delete_playlist(playlist_id=playlist_id)
