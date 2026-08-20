import pytest
from mimitune import (
    YTMusic,
    InnerTubeClient,
    PlaybackAuthState,
    YouTubeLocale,
    WEB_REMIX,
    SongItem,
    AlbumItem,
    ArtistItem,
    Artist,
    ArtistPage,
    LibraryPage,
    HistoryPage,
    TranscriptCue,
)
from mimitune.parsers import (
    parse_search_summary_response,
    parse_search_response,
    parse_album_response,
    parse_artist_response,
    parse_library_response,
    parse_history_response,
    parse_transcript_response,
    parse_account_menu_response,
    parse_next_response,
)


def test_auth_state():
    auth = PlaybackAuthState(cookie="SAPISID=12345; __Secure-3PAPISID=abc;")
    assert auth.has_login_cookie is True

    empty_auth = PlaybackAuthState()
    assert empty_auth.has_login_cookie is False


def test_client_headers():
    auth = PlaybackAuthState(cookie="SAPISID=test_sapisid;", visitor_data="Cgt123")
    client = InnerTubeClient(auth_state=auth)
    headers = client._build_headers(WEB_REMIX, set_login=True)

    assert headers["X-YouTube-Client-Name"] == "67"
    assert headers["X-Goog-Visitor-Id"] == "Cgt123"
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("SAPISIDHASH ")


def test_parse_search_summary():
    mock_response = {
        "contents": {
            "tabbedSearchResultsRenderer": {
                "tabs": [
                    {
                        "tabRenderer": {
                            "content": {
                                "sectionListRenderer": {
                                    "contents": [
                                        {
                                            "musicShelfRenderer": {
                                                "title": {"runs": [{"text": "Songs"}]},
                                                "contents": [
                                                    {
                                                        "musicResponsiveListItemRenderer": {
                                                            "flexColumns": [
                                                                {
                                                                    "musicResponsiveListItemFlexColumnRenderer": {
                                                                        "text": {"runs": [{"text": "Song Title"}]}
                                                                    }
                                                                },
                                                                {
                                                                    "musicResponsiveListItemFlexColumnRenderer": {
                                                                        "text": {"runs": [{"text": "Artist Name"}]}
                                                                    }
                                                                },
                                                            ],
                                                            "playlistItemData": {"videoId": "test_video_id"},
                                                        }
                                                    }
                                                ],
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                ]
            }
        }
    }

    result = parse_search_summary_response(mock_response)
    assert len(result.summaries) == 1
    assert result.summaries[0].title == "Songs"
    assert len(result.summaries[0].items) == 1
    song = result.summaries[0].items[0]
    assert isinstance(song, SongItem)
    assert song.id == "test_video_id"
    assert song.title == "Song Title"
    assert song.artists[0].name == "Artist Name"


def test_parse_artist_response():
    mock_response = {
        "header": {
            "musicImmersiveHeaderRenderer": {
                "title": {"runs": [{"text": "Artist Title"}]},
                "description": {"runs": [{"text": "Artist Description"}]},
                "subscriptionButton": {
                    "subscribeButtonRenderer": {
                        "channelId": "UC12345",
                        "subscriberCountText": {"runs": [{"text": "1M subscribers"}]},
                    }
                },
            }
        },
        "contents": {
            "singleColumnBrowseResultsRenderer": {
                "tabs": [
                    {
                        "tabRenderer": {
                            "content": {
                                "sectionListRenderer": {
                                    "contents": [
                                        {
                                            "musicShelfRenderer": {
                                                "title": {"runs": [{"text": "Top Songs"}]},
                                                "contents": [
                                                    {
                                                        "musicResponsiveListItemRenderer": {
                                                            "flexColumns": [
                                                                {
                                                                    "musicResponsiveListItemFlexColumnRenderer": {
                                                                        "text": {"runs": [{"text": "Song 1"}]}
                                                                    }
                                                                }
                                                            ],
                                                            "playlistItemData": {"videoId": "v1"},
                                                        }
                                                    }
                                                ],
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                ]
            }
        },
    }

    artist_page = parse_artist_response(mock_response, browse_id="UC12345")
    assert artist_page.artist.title == "Artist Title"
    assert artist_page.artist.channel_id == "UC12345"
    assert artist_page.description == "Artist Description"
    assert len(artist_page.sections) == 1
    assert artist_page.sections[0].title == "Top Songs"


def test_parse_transcript():
    mock_response = {
        "actions": [
            {
                "updateEngagementPanelAction": {
                    "content": {
                        "transcriptRenderer": {
                            "body": {
                                "transcriptBodyRenderer": {
                                    "cueGroups": [
                                        {
                                            "transcriptCueGroupRenderer": {
                                                "cues": [
                                                    {
                                                        "transcriptCueRenderer": {
                                                            "startOffsetMs": "15000",
                                                            "cue": {"simpleText": "♪ First lyric line"},
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        ]
    }

    cues = parse_transcript_response(mock_response)
    assert len(cues) == 1
    assert cues[0].time_ms == 15000
    assert cues[0].text == "First lyric line"


def test_parse_account_menu():
    mock_response = {
        "actions": [
            {
                "openPopupAction": {
                    "popup": {
                        "multiPageMenuRenderer": {
                            "header": {
                                "activeAccountHeaderRenderer": {
                                    "accountName": {"runs": [{"text": "Test User"}]},
                                    "accountHandle": {"runs": [{"text": "@testuser"}]},
                                }
                            }
                        }
                    }
                }
            }
        ]
    }

    account_info = parse_account_menu_response(mock_response)
    assert account_info.name == "Test User"
    assert account_info.handle == "@testuser"


def test_ytmusic_init():
    yt = YTMusic(cookie="SAPISID=xyz;", visitor_data="Cgt456")
    assert yt.client.auth_state.cookie == "SAPISID=xyz;"
    assert yt.client.auth_state.visitor_data == "Cgt456"
