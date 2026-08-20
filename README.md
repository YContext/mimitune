# opentune-ytmusic

A Python client library for YouTube Music, rewritten from the OpenTune Android app's InnerTube implementation.

## Installation

```bash
pip install opentune-ytmusic
```

## Quick Start

```python
from opentune_ytmusic import YTMusic

# Create a client (no auth required for basic usage)
yt = YTMusic()

# Search for songs
results = yt.search("Bohemian Rhapsody")
for song in results.items:
    print(f"{song.title} - {[a.name for a in song.artists]}")

# Get search summary (grouped results)
summary = yt.search_summary("Radiohead")
for group in summary.summaries:
    print(f"\n{group.title}:")
    for item in group.items:
        print(f"  {getattr(item, 'title', 'N/A')}")
```

## Authentication

Some features (library, playlists, likes) require authentication via cookies:

```python
from opentune_ytmusic import YTMusic

yt = YTMusic(
    cookie="SAPISID=your_sapisid_value; __Secure-3PAPISID=your_value;",
    visitor_data="your_visitor_data",
)

# Access your library
library = yt.get_library()
for item in library.items:
    print(f"{getattr(item, 'title', 'N/A')}")

# Access history
history = yt.get_history()
for section in history.sections:
    print(f"{section.title}:")
    for song in section.items:
        print(f"  {song.title}")
```

## API Reference

### `YTMusic(cookie=None, visitor_data=None, po_token=None, proxy=None)`

Main client class.

| Parameter | Type | Description |
|-----------|------|-------------|
| `cookie` | `str` | YouTube cookie string for authentication |
| `visitor_data` | `str` | Visitor data for authenticated requests |
| `po_token` | `str` | Proof of origin token for playback |
| `proxy` | `str` | HTTP proxy URL |

### Search

```python
# Basic search
results = yt.search("query")

# Search with filter (e.g., songs only)
results = yt.search("query", filter_param="EgIQAQ%3D%3D")

# Paginated search
results = yt.search("query", continuation=next_continuation)
```

### Browse

```python
# Album
album = yt.get_album("MPREb_xxxxx")
print(album.album.title, album.album.artists)
for song in album.songs:
    print(f"  {song.title}")

# Artist
artist = yt.get_artist("UCxxxxxx")
print(artist.artist.title)
for section in artist.sections:
    print(f"  {section.title}: {len(section.items)} items")

# Playlist
playlist = yt.get_playlist("VLPLxxxxxx")
print(playlist.playlist.title)
for song in playlist.songs:
    print(f"  {song.title}")

# Explore (new releases)
explore = yt.get_explore()
for album in explore.new_release_albums:
    print(f"{album.title} ({album.year})")

# Charts
charts = yt.get_charts()
for section in charts.sections:
    print(f"{section.title}: {len(section.items)} items")
```

### Player & Metadata

```python
# Get player info (streaming data, etc.)
player = yt.get_player("video_id_here")
print(player.playability_status)

# Get next/suggested videos
next_result = yt.get_next("video_id_here")
for song in next_result.items:
    print(f"{song.title}")

# Get lyrics
lyrics = yt.get_lyrics("lyrics_browse_id")
print(lyrics)

# Get transcript
transcript = yt.get_transcript("video_id_here")
for cue in transcript:
    print(f"[{cue.time_ms}ms] {cue.text}")

# Get detailed media info
info = yt.get_media_info("video_id_here")
print(f"{info.title} by {info.author}")
print(f"Views: {info.view_count}, Likes: {info.like}")
```

### Library Management (requires auth)

```python
# Create playlist
playlist_id = yt.create_playlist("My New Playlist")

# Add song to playlist
yt.add_to_playlist(playlist_id, "video_id")

# Remove song from playlist
yt.remove_from_playlist(playlist_id, "video_id", "set_video_id")

# Delete playlist
yt.delete_playlist(playlist_id)

# Subscribe to channel
yt.subscribe_channel("UCxxxxxx", subscribe=True)

# Like/unlike video
yt.like_video("video_id", like=True)
```

### Proxy Support

```python
yt = YTMusic(proxy="http://proxy:8080")

# Or set later
yt.set_proxy("socks5://proxy:1080")
```

## Low-Level Client

For direct InnerTube API access:

```python
from opentune_ytmusic import InnerTubeClient, WEB_REMIX

client = InnerTubeClient(default_client=WEB_REMIX)

# Raw search
response = client.search(query="Radiohead")

# Raw browse
response = client.browse(browse_id="UCxxxxxx")

# Raw player
response = client.player(video_id="xxxxxx")
```

## Data Models

All responses use typed dataclasses:

- `SongItem` - Song with id, title, artists, duration, thumbnail
- `AlbumItem` - Album with browse_id, title, artists, year
- `ArtistItem` - Artist with id, title, subscriber_count
- `PlaylistItem` - Playlist with id, title, author
- `SearchResult` - List of items with optional continuation
- `AlbumPage` - Album with songs list
- `ArtistPage` - Artist with sections
- `PlaylistPage` - Playlist with songs
- `PlayerResponse` - Streaming data and playability status
- `MediaInfo` - Video metadata with view/like counts

## License

GPL-3.0 - See [LICENSE](LICENSE) for details.
