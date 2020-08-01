import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import ffmpeg
import m3u8
import requests
from const import Const

from radiko.authorization import Authorization


class RadikoRecorder:
    MASTER_PLAYLIST_BASE_URL = "https://rpaa.smartstream.ne.jp/so/playlist.m3u8"
    DUMMY_LSID = "11111111111111111111111111111111111111"  # Radiko APIの仕様で38桁の文字列が必要。

    def __init__(self, station: str, program: str, record_time: int, output_file_path: Path) -> None:
        self.station = station
        self.program = program
        self.record_time = record_time
        self.output_file_path = output_file_path
        logging.debug(f"STATION:{station}\tPROGRAM:{program}\tRECORD_TIME:{record_time}")
        self.headers: Dict[str, str] = self._make_headers()

    def _make_headers(self) -> Dict[str, str]:
        """HTTPリクエストのヘッダーを作成する
        """
        headers: Dict[str, str] = Authorization().get_auththenticated_headers()
        headers["Connection"] = "keep-alive"
        logging.debug(f"headers: {headers}")
        return headers

    def _make_master_playlist_url(self) -> str:
        """master playlistのURLを作成する
        """
        params: List[str] = [
            f"station_id={self.station}",
            "l=15",
            f"lsid={RadikoRecorder.DUMMY_LSID}",
            "type=b",
        ]
        url = f"{RadikoRecorder.MASTER_PLAYLIST_BASE_URL}?" + "&".join(params)
        logging.debug(f"playlist url:{url}")
        return url

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
        media_playlist_url = m3u8_obj.playlists[0].uri
        logging.debug(f"media_playlist_url: {media_playlist_url}")
        return media_playlist_url

    def _get_media_url(self, media_playlist_url) -> List[Tuple[str, str]]:
        """音声ファイルのURLをmedia playlistから取得する
        """
        query_time = int(datetime.now(tz=Const.JST).timestamp() * 100)
        logging.debug(f"aac url:{media_playlist_url}&_={query_time}")

        response = requests.get(url=f"{media_playlist_url}&_={query_time}", headers=self.headers)
        if response.status_code != 200:
            return None

        m3u8_obj = m3u8.loads(str(response.content.decode("utf-8")))
        return [(s.program_date_time, s.uri) for s in m3u8_obj.segments]

    def _make_audio_headers(self) -> str:
        """音声取得用 HTTP リクエストのヘッダーを作成する
        requests 用の HTTP ヘッダーをもとに ffmpeg 用に文字列の HTTP リクエストヘッダーを作る
        """
        header_list: List[str] = [f"{k}: {v}" for k, v in self.headers.items()]
        audio_headers = "\r\n".join(header_list) + "\r\n"
        logging.debug(f"audio headers: {audio_headers}")
        return audio_headers

    def _record(self) -> None:
        logging.info(f"START_RECORD\tOUTPUT_FILE_PATH:{self.output_file_path}")

        media_playlist_url = self._get_media_playlist_url()
        end = datetime.now() + timedelta(minutes=self.record_time)
        recorded = set()

        while datetime.now() <= end:
            url_list: List[Tuple[str, str]] = self._get_media_url(media_playlist_url)
            if url_list is None:
                # 時間をおいてリトライすると取れるときがあるため待つ
                time.sleep(3.0)
                continue

            headers: str = self._make_audio_headers()
            # m3u8 ファイルに記述されている音声ファイルを重複しないように取得する
            for dt, url in url_list:
                if dt in recorded:
                    continue

                if not os.path.isdir("./tmp"):
                    os.mkdir("./tmp")
                try:
                    ffmpeg.input(filename=url, f="aac", headers=headers).output(filename=f"./tmp/{dt}.aac").run(
                        capture_stdout=True
                    )
                except Exception as e:
                    logging.warning("failed in run ffmpeg")
                    logging.warning(e)
                recorded.add(dt)
            time.sleep(5.0)

        logging.debug("record end")
        return recorded

    def execute(self):
        recorded = self._record()

        sorted_recorded = sorted(recorded)
        files = [f"./tmp/{e}.aac" for e in sorted_recorded]
        logging.debug(files)
        try:
            streams = [ffmpeg.input(filename=f) for f in files]
            ffmpeg.concat(*streams, a=1, v=0).output(filename=self.output_file_path, absf="aac_adtstoasc").run(
                capture_stdout=True
            )
        except Exception as e:
            logging.warning("failed in run ffmpeg concat")
            logging.warning(e)
        for f in files:
            os.remove(f)
