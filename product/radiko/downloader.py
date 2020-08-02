import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Set, Tuple

import ffmpeg

from .playlist import Playlist


class Downloader:
    @classmethod
    def execute(cls, station: str, record_time: int, temp_dir_path: Path) -> Set[str]:
        playlist = Playlist(station)

        end = datetime.now() + timedelta(minutes=record_time)
        headers: str = playlist.get_audio_headers()
        filepaths: Set[str] = set()
        while datetime.now() <= end:
            url_list: List[Tuple[str, str]] = playlist.get_media_url()
            if url_list is None:
                # 時間をおいてリトライすると取れるときがあるため待つ
                time.sleep(3.0)
                continue

            for dt, url in url_list:
                filepath = temp_dir_path.joinpath(f"{dt}.aac")
                if filepath in filepaths:
                    continue

                try:
                    ffmpeg.input(filename=url, f="aac", headers=headers).output(filename=filepath).run(
                        capture_stdout=True
                    )
                    filepaths.add(filepath)
                except Exception as e:
                    logging.warning("failed in run ffmpeg")
                    logging.warning(e)
            time.sleep(5.0)

        return sorted(filepaths)
