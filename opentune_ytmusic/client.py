"""
InnerTube HTTP client for communicating directly with YouTube Music endpoints.
"""

import base64
import hashlib
import time
import urllib.parse
from typing import Dict, Any, Optional, List, Union
import httpx

from opentune_ytmusic.models import (
    YouTubeLocale,
    PlaybackAuthState,
    YouTubeClientPreset,
    WEB,
    WEB_REMIX,
)


def calculate_sapisid_hash(sapisid: str, origin: str, timestamp: int) -> str:
    payload = f"{timestamp} {sapisid} {origin}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def parse_cookie_string(cookie_str: str) -> Dict[str, str]:
    cookies = {}
    for item in cookie_str.split(";"):
        if "=" in item:
            k, v = item.strip().split("=", 1)
            cookies[k] = v
    return cookies


class InnerTubeClient:
    def __init__(
        self,
        locale: Optional[YouTubeLocale] = None,
        auth_state: Optional[PlaybackAuthState] = None,
        default_client: YouTubeClientPreset = WEB_REMIX,
        timeout: float = 15.0,
        proxy: Optional[str] = None,
    ):
        self.locale = locale or YouTubeLocale()
        self.auth_state = auth_state or PlaybackAuthState()
        self.default_client = default_client
        self.timeout = timeout
        self.proxy = proxy

    def set_proxy(self, proxy: Optional[str]) -> None:
        self.proxy = proxy

    def _get_http_client(self) -> httpx.Client:
        return httpx.Client(
            proxy=self.proxy,
            timeout=self.timeout,
            headers={"Accept-Encoding": "gzip, deflate"},
        )

    def _build_context(
        self,
        client: YouTubeClientPreset,
        set_login: bool = False,
        override_locale: Optional[YouTubeLocale] = None,
    ) -> Dict[str, Any]:
        loc = override_locale or self.locale
        client_ctx = {
            "clientName": client.client_name,
            "clientVersion": client.client_version,
            "gl": loc.gl,
            "hl": loc.hl,
        }
        if client.os_name:
            client_ctx["osName"] = client.os_name
        if client.os_version:
            client_ctx["osVersion"] = client.os_version
        if client.device_make:
            client_ctx["deviceMake"] = client.device_make
        if client.device_model:
            client_ctx["deviceModel"] = client.device_model
        if client.android_sdk_version:
            client_ctx["androidSdkVersion"] = client.android_sdk_version
        if self.auth_state.visitor_data:
            client_ctx["visitorData"] = self.auth_state.visitor_data

        user_ctx = {}
        if set_login and client.login_supported and self.auth_state.data_sync_id:
            user_ctx["onBehalfOfUser"] = self.auth_state.data_sync_id

        return {
            "client": client_ctx,
            "user": user_ctx,
        }

    def _build_headers(
        self,
        client: YouTubeClientPreset,
        set_login: bool = False,
    ) -> Dict[str, str]:
        origin = client.request_origin()
        referer = client.request_referer()

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Format-Version": "1",
            "X-YouTube-Client-Name": client.client_id,
            "X-YouTube-Client-Version": client.client_version,
            "X-Origin": origin,
            "Referer": referer,
            "User-Agent": client.user_agent,
        }

        if self.auth_state.visitor_data:
            headers["X-Goog-Visitor-Id"] = self.auth_state.visitor_data

        if set_login and client.login_supported and self.auth_state.cookie:
            headers["cookie"] = self.auth_state.cookie
            cookie_map = parse_cookie_string(self.auth_state.cookie)
            sapisid = cookie_map.get("SAPISID") or cookie_map.get("__Secure-3PAPISID")
            if sapisid:
                now = int(time.time())
                sapisid_hash = calculate_sapisid_hash(sapisid, origin, now)
                headers["Authorization"] = f"SAPISIDHASH {now}_{sapisid_hash}"

        return headers

    def post(
        self,
        endpoint: str,
        body: Dict[str, Any],
        client: Optional[YouTubeClientPreset] = None,
        set_login: bool = False,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        preset = client or self.default_client
        url = f"{preset.request_origin()}/youtubei/v1/{endpoint}"

        queryParams = {"prettyPrint": "false"}
        if params:
            queryParams.update(params)

        headers = self._build_headers(preset, set_login=set_login)

        with self._get_http_client() as http:
            res = http.post(url, json=body, headers=headers, params=queryParams)
            res.raise_for_status()
            return res.json()

    def search(
        self,
        query: Optional[str] = None,
        params: Optional[str] = None,
        continuation: Optional[str] = None,
        client: Optional[YouTubeClientPreset] = None,
    ) -> Dict[str, Any]:
        preset = client or self.default_client
        body = {
            "context": self._build_context(preset),
            "query": query,
            "params": params,
        }
        qp = {}
        if continuation:
            qp["continuation"] = continuation
            qp["ctoken"] = continuation
        return self.post("search", body, client=preset, params=qp)

    def browse(
        self,
        browse_id: Optional[str] = None,
        params: Optional[str] = None,
        continuation: Optional[str] = None,
        set_login: bool = False,
        client: Optional[YouTubeClientPreset] = None,
    ) -> Dict[str, Any]:
        preset = client or self.default_client
        body = {
            "context": self._build_context(preset, set_login=set_login),
            "browseId": browse_id,
            "params": params,
            "continuation": continuation,
        }
        return self.post("browse", body, client=preset, set_login=set_login)

    def player(
        self,
        video_id: str,
        playlist_id: Optional[str] = None,
        signature_timestamp: Optional[int] = None,
        po_token: Optional[str] = None,
        set_login: bool = True,
        client: Optional[YouTubeClientPreset] = None,
    ) -> Dict[str, Any]:
        preset = client or self.default_client
        ctx = self._build_context(preset, set_login=set_login)
        if preset.is_embedded:
            ctx["thirdParty"] = {"embedUrl": f"https://www.youtube.com/watch?v={video_id}"}

        body: Dict[str, Any] = {
            "context": ctx,
            "videoId": video_id,
            "playlistId": playlist_id,
        }

        if preset.use_signature_timestamp and signature_timestamp is not None:
            body["playbackContext"] = {
                "contentPlaybackContext": {
                    "signatureTimestamp": signature_timestamp
                }
            }

        resolved_po_token = po_token or self.auth_state.po_token
        if resolved_po_token:
            body["serviceIntegrityDimensions"] = {"poToken": resolved_po_token}

        return self.post("player", body, client=preset, set_login=set_login)

    def next(
        self,
        video_id: Optional[str] = None,
        playlist_id: Optional[str] = None,
        playlist_set_video_id: Optional[str] = None,
        index: Optional[int] = None,
        params: Optional[str] = None,
        continuation: Optional[str] = None,
        client: Optional[YouTubeClientPreset] = None,
    ) -> Dict[str, Any]:
        preset = client or self.default_client
        queue_locale = YouTubeLocale(gl="US", hl="en")
        body = {
            "context": self._build_context(preset, set_login=True, override_locale=queue_locale),
            "videoId": video_id,
            "playlistId": playlist_id,
            "playlistSetVideoId": playlist_set_video_id,
            "index": index,
            "params": params,
            "continuation": continuation,
        }
        return self.post("next", body, client=preset, set_login=True)

    def get_search_suggestions(
        self,
        input_str: str,
        client: Optional[YouTubeClientPreset] = None,
    ) -> Dict[str, Any]:
        preset = client or self.default_client
        body = {
            "context": self._build_context(preset),
            "input": input_str,
        }
        return self.post("music/get_search_suggestions", body, client=preset)

    def get_transcript(self, video_id: str) -> Dict[str, Any]:
        preset = WEB
        encoded_params = base64.b64encode(f"\n\x0b{video_id}".encode("utf-8")).decode("utf-8")
        body = {
            "context": self._build_context(preset),
            "params": encoded_params,
        }
        url = "https://music.youtube.com/youtubei/v1/get_transcript"
        params = {"key": "AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX3"}
        headers = {
            "Content-Type": "application/json",
            "User-Agent": preset.user_agent,
        }
        with self._get_http_client() as http:
            res = http.post(url, json=body, headers=headers, params=params)
            res.raise_for_status()
            return res.json()

    def account_menu(self, client: Optional[YouTubeClientPreset] = None) -> Dict[str, Any]:
        preset = client or self.default_client
        body = {"context": self._build_context(preset, set_login=True)}
        return self.post("account/account_menu", body, client=preset, set_login=True)

    def subscribe_channel(self, channel_id: str, subscribe: bool = True, client: Optional[YouTubeClientPreset] = None) -> Dict[str, Any]:
        preset = client or self.default_client
        endpoint = "subscription/subscribe" if subscribe else "subscription/unsubscribe"
        body = {
            "context": self._build_context(preset, set_login=True),
            "channelIds": [channel_id],
        }
        return self.post(endpoint, body, client=preset, set_login=True)

    def like_video(self, video_id: str, like: bool = True, client: Optional[YouTubeClientPreset] = None) -> Dict[str, Any]:
        preset = client or self.default_client
        endpoint = "like/like" if like else "like/removelike"
        body = {
            "context": self._build_context(preset, set_login=True),
            "target": {"videoId": video_id},
        }
        return self.post(endpoint, body, client=preset, set_login=True)

    def like_playlist(self, playlist_id: str, like: bool = True, client: Optional[YouTubeClientPreset] = None) -> Dict[str, Any]:
        preset = client or self.default_client
        endpoint = "like/like" if like else "like/removelike"
        body = {
            "context": self._build_context(preset, set_login=True),
            "target": {"playlistId": playlist_id},
        }
        return self.post(endpoint, body, client=preset, set_login=True)

    def edit_playlist(
        self,
        playlist_id: str,
        actions: List[Dict[str, Any]],
        client: Optional[YouTubeClientPreset] = None,
    ) -> Dict[str, Any]:
        preset = client or self.default_client
        clean_id = playlist_id.removeprefix("VL")
        body = {
            "context": self._build_context(preset, set_login=True),
            "playlistId": clean_id,
            "actions": actions,
        }
        return self.post("browse/edit_playlist", body, client=preset, set_login=True)

    def create_playlist(
        self,
        title: str,
        client: Optional[YouTubeClientPreset] = None,
    ) -> Dict[str, Any]:
        preset = client or self.default_client
        body = {
            "context": self._build_context(preset, set_login=True),
            "title": title,
        }
        return self.post("playlist/create", body, client=preset, set_login=True)

    def delete_playlist(
        self,
        playlist_id: str,
        client: Optional[YouTubeClientPreset] = None,
    ) -> Dict[str, Any]:
        preset = client or self.default_client
        body = {
            "context": self._build_context(preset, set_login=True),
            "playlistId": playlist_id,
        }
        return self.post("playlist/delete", body, client=preset, set_login=True)

    def register_playback(
        self,
        playback_url: str,
        cpn: str,
        playlist_id: Optional[str] = None,
        po_token: Optional[str] = None,
        client: Optional[YouTubeClientPreset] = None,
    ) -> httpx.Response:
        preset = client or self.default_client
        url = playback_url.replace("https://s.youtube.com", "https://music.youtube.com")
        params = {
            "ver": "2",
            "c": preset.client_name,
            "cpn": cpn,
        }
        resolved_po = po_token or self.auth_state.po_token
        if resolved_po:
            params["pot"] = resolved_po
        if playlist_id:
            params["list"] = playlist_id
            params["referrer"] = f"https://music.youtube.com/playlist?list={playlist_id}"

        headers = self._build_headers(preset, set_login=True)
        with self._get_http_client() as http:
            res = http.get(url, headers=headers, params=params)
            res.raise_for_status()
            return res
