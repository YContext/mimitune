"""
Parsers for transforming InnerTube API JSON responses into structured models.
"""

from typing import List, Optional, Dict, Any
from opentune_ytmusic.models import (
    SongItem, AlbumItem, ArtistItem, PlaylistItem, Artist,
    SearchSummary, SearchSummaryPage, SearchResult,
    AlbumPage, PlaylistPage, HomeSection, HomePage,
    ExplorePage, ChartSection, ChartsPage, AccountInfo, NextResult
)


def safe_get(data: Optional[Dict[str, Any]], *keys: str, default: Any = None) -> Any:
    curr = data
    for k in keys:
        if not isinstance(curr, dict):
            return default
        curr = curr.get(k)
        if curr is None:
            return default
    return curr if curr is not None else default


def extract_runs_text(runs_obj: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(runs_obj, dict) or "runs" not in runs_obj:
        return None
    runs = runs_obj.get("runs") or []
    return "".join(run.get("text", "") for run in runs if isinstance(run, dict))


def extract_artist_runs(runs_obj: Optional[Dict[str, Any]]) -> List[Artist]:
    if not isinstance(runs_obj, dict) or "runs" not in runs_obj:
        return []
    artists = []
    runs = runs_obj.get("runs") or []
    for run in runs:
        if not isinstance(run, dict):
            continue
        text = run.get("text", "").strip()
        if not text or text in (",", "&", "•"):
            continue
        browse_id = safe_get(run, "navigationEndpoint", "browseEndpoint", "browseId")
        artists.append(Artist(name=text, id=browse_id))
    return artists


def extract_thumbnail_url(thumbnail_renderer: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(thumbnail_renderer, dict):
        return None
    renderer = thumbnail_renderer.get("musicThumbnailRenderer") or thumbnail_renderer
    if not isinstance(renderer, dict):
        return None
    thumbnails = safe_get(renderer, "thumbnail", "thumbnails") or renderer.get("thumbnails")
    if isinstance(thumbnails, list) and len(thumbnails) > 0:
        last = thumbnails[-1]
        if isinstance(last, dict):
            return last.get("url")
    return None


def parse_responsive_list_item(item: Dict[str, Any]) -> Optional[Any]:
    if not isinstance(item, dict):
        return None
    renderer = item.get("musicResponsiveListItemRenderer")
    if not isinstance(renderer, dict):
        return None

    flex_columns = renderer.get("flexColumns") or []
    title_run = None
    if flex_columns and isinstance(flex_columns, list):
        first_col = safe_get(flex_columns[0], "musicResponsiveListItemFlexColumnRenderer")
        if isinstance(first_col, dict):
            title_run = first_col.get("text")

    title = extract_runs_text(title_run) or ""

    nav_endpoint = renderer.get("navigationEndpoint") or {}
    watch_endpoint = nav_endpoint.get("watchEndpoint") or {}
    browse_endpoint = nav_endpoint.get("browseEndpoint") or {}

    video_id = watch_endpoint.get("videoId") or safe_get(renderer, "playlistItemData", "videoId")

    thumbnail = extract_thumbnail_url(renderer.get("thumbnail"))
    badges = renderer.get("badges") or []
    explicit = any(
        safe_get(b, "musicInlineBadgeRenderer", "icon", "iconType") == "MUSIC_EXPLICIT_BADGE"
        for b in badges if isinstance(b, dict)
    )

    if video_id:
        artists = []
        if len(flex_columns) > 1:
            second_col = safe_get(flex_columns[1], "musicResponsiveListItemFlexColumnRenderer")
            if isinstance(second_col, dict):
                artists = extract_artist_runs(second_col.get("text"))

        set_video_id = safe_get(renderer, "playlistItemData", "playlistSetVideoId")

        return SongItem(
            id=video_id,
            title=title,
            artists=artists,
            thumbnail=thumbnail,
            explicit=explicit,
            set_video_id=set_video_id,
        )

    if browse_endpoint:
        browse_id = browse_endpoint.get("browseId", "")
        if browse_id.startswith("FEmusic_library_") or browse_id.startswith("MPREb_") or browse_id.startswith("VL"):
            if browse_id.startswith("MPREb_"):
                return AlbumItem(
                    browse_id=browse_id,
                    playlist_id=browse_id,
                    title=title,
                    thumbnail=thumbnail,
                    explicit=explicit,
                )
            else:
                return PlaylistItem(
                    id=browse_id,
                    title=title,
                    thumbnail=thumbnail,
                )
        elif browse_id.startswith("UC") or browse_id.startswith("FEmusic_artist_"):
            return ArtistItem(
                id=browse_id,
                title=title,
                thumbnail=thumbnail,
            )

    return None


def parse_two_row_item(renderer: Dict[str, Any]) -> Optional[Any]:
    if not isinstance(renderer, dict):
        return None
    title = extract_runs_text(renderer.get("title")) or ""
    thumbnail = extract_thumbnail_url(renderer.get("thumbnailRenderer"))
    nav_endpoint = renderer.get("navigationEndpoint") or {}
    watch_endpoint = nav_endpoint.get("watchEndpoint") or {}
    browse_endpoint = nav_endpoint.get("browseEndpoint") or {}

    subtitle_runs = renderer.get("subtitle") or {}
    artists = extract_artist_runs(subtitle_runs)

    subtitle_badges = renderer.get("subtitleBadges") or []
    explicit = any(
        safe_get(b, "musicInlineBadgeRenderer", "icon", "iconType") == "MUSIC_EXPLICIT_BADGE"
        for b in subtitle_badges if isinstance(b, dict)
    )

    if watch_endpoint and "videoId" in watch_endpoint:
        return SongItem(
            id=watch_endpoint["videoId"],
            title=title,
            artists=artists,
            thumbnail=thumbnail,
            explicit=explicit,
        )

    if browse_endpoint and "browseId" in browse_endpoint:
        browse_id = browse_endpoint["browseId"]
        if browse_id.startswith("MPREb_") or "playlistId" in (nav_endpoint.get("watchPlaylistEndpoint") or {}):
            playlist_id = safe_get(
                renderer,
                "thumbnailOverlay",
                "musicItemThumbnailOverlayRenderer",
                "content",
                "musicPlayButtonRenderer",
                "playNavigationEndpoint",
                "watchPlaylistEndpoint",
                "playlistId",
                default=browse_id
            )
            return AlbumItem(
                browse_id=browse_id,
                playlist_id=playlist_id,
                title=title,
                artists=artists,
                thumbnail=thumbnail,
                explicit=explicit,
            )
        elif browse_id.startswith("UC") or browse_id.startswith("FEmusic_artist_"):
            return ArtistItem(
                id=browse_id,
                title=title,
                thumbnail=thumbnail,
            )
        elif browse_id.startswith("VL") or browse_id.startswith("PL"):
            return PlaylistItem(
                id=browse_id,
                title=title,
                thumbnail=thumbnail,
            )

    return None


def parse_search_summary_response(response: Dict[str, Any]) -> SearchSummaryPage:
    contents = safe_get(
        response,
        "contents",
        "tabbedSearchResultsRenderer",
        "tabs",
        default=[]
    )
    if contents and isinstance(contents, list):
        contents = safe_get(
            contents[0],
            "tabRenderer",
            "content",
            "sectionListRenderer",
            "contents",
            default=[]
        )
    else:
        contents = []

    top_items = []
    summaries = []

    for content in contents:
        if not isinstance(content, dict):
            continue
        card_shelf = content.get("musicCardShelfRenderer")
        if card_shelf:
            card_item = parse_responsive_list_item({"musicResponsiveListItemRenderer": card_shelf}) or parse_two_row_item(card_shelf)
            shelf_items = []
            if card_item:
                shelf_items.append(card_item)
            for inner in card_shelf.get("contents") or []:
                parsed = parse_responsive_list_item(inner)
                if parsed:
                    shelf_items.append(parsed)
            if shelf_items:
                top_items.extend(shelf_items)
            continue

        music_shelf = content.get("musicShelfRenderer")
        if music_shelf:
            shelf_title = extract_runs_text(music_shelf.get("title")) or "Results"
            shelf_items = []
            for item in music_shelf.get("contents") or []:
                parsed = parse_responsive_list_item(item)
                if parsed:
                    shelf_items.append(parsed)
            if shelf_items:
                summaries.append(SearchSummary(title=shelf_title, items=shelf_items))

    result_summaries = []
    if top_items:
        result_summaries.append(SearchSummary(title="Top results", items=top_items))
    result_summaries.extend(summaries)

    return SearchSummaryPage(summaries=result_summaries)


def parse_search_response(response: Dict[str, Any]) -> SearchResult:
    tabs = safe_get(response, "contents", "tabbedSearchResultsRenderer", "tabs", default=[])
    contents = safe_get(
        tabs[0] if tabs and isinstance(tabs, list) else {},
        "tabRenderer",
        "content",
        "sectionListRenderer",
        "contents",
        default=[]
    )

    items = []
    continuation = None

    for content in contents:
        if not isinstance(content, dict):
            continue
        music_shelf = content.get("musicShelfRenderer")
        if music_shelf:
            for item in music_shelf.get("contents") or []:
                parsed = parse_responsive_list_item(item)
                if parsed:
                    items.append(parsed)
            if "continuations" in music_shelf:
                conts = music_shelf["continuations"]
                if conts and isinstance(conts, list) and len(conts) > 0:
                    continuation = safe_get(conts[0], "nextContinuationData", "continuation")

    return SearchResult(items=items, continuation=continuation)


def parse_album_response(response: Dict[str, Any], browse_id: str) -> AlbumPage:
    two_col = safe_get(response, "contents", "twoColumnBrowseResultsRenderer", default={})
    header = safe_get(response, "header", "musicDetailHeaderRenderer") or safe_get(response, "header", "musicResponsiveHeaderRenderer")

    title = "Unknown Album"
    thumbnail = None
    artists = []
    year = None

    if header:
        title = extract_runs_text(header.get("title")) or title
        thumbnail = extract_thumbnail_url(header.get("thumbnail"))
        subtitle = header.get("subtitle") or header.get("straplineTextOne")
        artists = extract_artist_runs(subtitle)

    songs = []
    sec_contents = safe_get(two_col, "secondaryContents", "sectionListRenderer", "contents", default=[])
    for sec in sec_contents:
        if not isinstance(sec, dict):
            continue
        shelf = sec.get("musicPlaylistShelfRenderer") or sec.get("musicShelfRenderer")
        if shelf:
            for item in shelf.get("contents") or []:
                parsed = parse_responsive_list_item(item)
                if isinstance(parsed, SongItem):
                    songs.append(parsed)

    album_item = AlbumItem(
        browse_id=browse_id,
        playlist_id=browse_id,
        title=title,
        artists=artists,
        year=year,
        thumbnail=thumbnail,
    )

    return AlbumPage(album=album_item, songs=songs)


def parse_playlist_response(response: Dict[str, Any], playlist_id: str) -> PlaylistPage:
    two_col = safe_get(response, "contents", "twoColumnBrowseResultsRenderer", default={})
    tabs = two_col.get("tabs") or []
    base = safe_get(
        tabs[0] if tabs and isinstance(tabs, list) else {},
        "tabRenderer",
        "content",
        "sectionListRenderer",
        "contents",
        default=[{}]
    )
    first_base = base[0] if isinstance(base, list) and len(base) > 0 else {}

    header = first_base.get("musicResponsiveHeaderRenderer") or safe_get(
        first_base, "musicEditablePlaylistDetailHeaderRenderer", "header", "musicResponsiveHeaderRenderer"
    )

    title = "Unknown Playlist"
    thumbnail = None
    author = None

    if header:
        title = extract_runs_text(header.get("title")) or title
        thumbnail = extract_thumbnail_url(header.get("thumbnail"))
        strapline = header.get("straplineTextOne")
        artist_list = extract_artist_runs(strapline)
        if artist_list:
            author = artist_list[0]

    songs = []
    sec_contents = safe_get(two_col, "secondaryContents", "sectionListRenderer", "contents", default=[])
    for sec in sec_contents:
        if not isinstance(sec, dict):
            continue
        shelf = sec.get("musicPlaylistShelfRenderer")
        if shelf:
            for item in shelf.get("contents") or []:
                parsed = parse_responsive_list_item(item)
                if isinstance(parsed, SongItem):
                    songs.append(parsed)

    playlist_item = PlaylistItem(
        id=playlist_id,
        title=title,
        author=author,
        thumbnail=thumbnail,
    )

    return PlaylistPage(playlist=playlist_item, songs=songs)


def parse_account_menu_response(response: Dict[str, Any]) -> AccountInfo:
    actions = response.get("actions") or []
    if not actions or not isinstance(actions, list):
        return AccountInfo()

    popup = safe_get(
        actions[0] if isinstance(actions[0], dict) else {},
        "openPopupAction",
        "popup",
        "multiPageMenuRenderer",
        "header",
        "activeAccountHeaderRenderer",
        default={}
    )

    account_name = extract_runs_text(popup.get("accountName"))
    handle = extract_runs_text(popup.get("accountHandle"))

    return AccountInfo(
        name=account_name,
        handle=handle,
    )


def parse_next_response(response: Dict[str, Any]) -> NextResult:
    tabs = safe_get(
        response,
        "contents",
        "singleColumnMusicWatchNextResultsRenderer",
        "tabbedRenderer",
        "watchNextTabbedResultsRenderer",
        "tabs",
        default=[]
    )
    first_tab = tabs[0] if tabs and isinstance(tabs, list) else {}

    queue_renderer = safe_get(
        first_tab,
        "tabRenderer",
        "content",
        "musicQueueRenderer",
        default={}
    )

    results = safe_get(
        queue_renderer,
        "content",
        "playlistPanelRenderer",
        default={}
    )

    title = extract_runs_text(safe_get(queue_renderer, "header", "musicQueueHeaderRenderer", "subtitle"))

    items = []
    current_index = None

    contents = results.get("contents") or []
    for idx, content in enumerate(contents):
        if not isinstance(content, dict):
            continue
        panel_video = content.get("playlistPanelVideoRenderer")
        if panel_video:
            video_id = safe_get(panel_video, "navigationEndpoint", "watchEndpoint", "videoId", default="")
            song_title = extract_runs_text(panel_video.get("title")) or ""
            artists = extract_artist_runs(panel_video.get("shortBylineText"))
            thumbnail = extract_thumbnail_url(panel_video.get("thumbnail"))

            if panel_video.get("selected"):
                current_index = idx

            items.append(
                SongItem(
                    id=video_id,
                    title=song_title,
                    artists=artists,
                    thumbnail=thumbnail,
                )
            )

    return NextResult(
        title=title,
        items=items,
        current_index=current_index,
    )
