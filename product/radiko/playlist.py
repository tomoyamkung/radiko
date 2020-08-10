import logging
from datetime import datetime
from typing import Dict, List, Tuple

import m3u8
import requests
from const import Const

from radiko.authorization import Authorization


class Playlist:
    MASTER_PLAYLIST_BASE_URL = "https://rpaa.smartstream.ne.jp/so/playlist.m3u8"
    DUMMY_LSID = "11111111111111111111111111111111111111"  # Radiko APIの仕様で38桁の文字列が必要。

    def __init__(self, station: str) -> None:
        self.station = station
        self.headers: Dict[str, str] = self._make_headers()

    def _make_headers(self) -> Dict[str, str]:
        """HTTPリクエストのヘッダーを作成する
        """
        headers: Dict[str, str] = Authorization().get_auththenticated_headers()
        headers["Connection"] = "keep-alive"
        return headers

    def get_media_url(self) -> List[Tuple[str, str]]:
        """音声ファイルのURLをmedia playlistから取得する
        """
        media_playlist_url: str = self._get_media_playlist_url()
        query_time = int(datetime.now(tz=Const.JST).timestamp() * 100)
        response = requests.get(url=f"{media_playlist_url}&_={query_time}", headers=self.headers)
        if response.status_code != 200:
            return None

        m3u8_obj = m3u8.loads(str(response.content.decode("utf-8")))
        return [(s.program_date_time, s.uri) for s in m3u8_obj.segments]

    def _get_media_playlist_url(self) -> str:
        """media playlistのURLを取得する
        """
        url: str = self._make_master_playlist_url()
        response = requests.get(url=url, headers=self.headers)
        if response.status_code != 200:
            logging.warning("failed to get media playlist url")
            logging.warning(f"status_code:{response.status_code}")
            logging.warning(f"content:{response.content}")
            raise Exception("failed in radiko get media playlist")

        m3u8_obj = m3u8.loads(response.content.decode("utf-8"))
        return m3u8_obj.playlists[0].uri

    def _make_master_playlist_url(self) -> str:
        """master playlistのURLを作成する
        """
        params: List[str] = [
            f"station_id={self.station}",
            "l=15",
            f"lsid={Playlist.DUMMY_LSID}",
            "type=b",
        ]
        return f"{Playlist.MASTER_PLAYLIST_BASE_URL}?" + "&".join(params)

    def get_audio_headers(self) -> str:
        """音声取得用 HTTP リクエストのヘッダーを作成する
        requests 用の HTTP ヘッダーをもとに ffmpeg 用に文字列の HTTP リクエストヘッダーを作る
        """
        header_list: List[str] = [f"{k}: {v}" for k, v in self.headers.items()]
        return "\r\n".join(header_list) + "\r\n"
