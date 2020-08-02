import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import ffmpeg
from directory_mixin import DirectoryMixin
from settings import AUDIO_TEMPORARY_DIR_PATH

from .playlist import Playlist


class RadikoRecorder(DirectoryMixin):
    def __init__(self, station: str, program: str, record_time: int, output_file_path: Path) -> None:
        self.station = station
        self.program = program
        self.record_time = record_time
        self.output_file_path = output_file_path

    def _record(self, temp_dir_path: Path) -> None:
        logging.info(f"START_RECORD\tOUTPUT_FILE_PATH:{self.output_file_path}")

        playlist = Playlist(self.station)
        end = datetime.now() + timedelta(minutes=self.record_time)
        recorded = set()
        while datetime.now() <= end:
            url_list: List[Tuple[str, str]] = playlist.get_media_url()
            if url_list is None:
                # 時間をおいてリトライすると取れるときがあるため待つ
                time.sleep(3.0)
                continue

            headers: str = playlist.get_audio_headers()
            # m3u8 ファイルに記述されている音声ファイルを重複しないように取得する
            for dt, url in url_list:
                if dt in recorded:
                    continue

                filename = temp_dir_path.joinpath(f"{dt}.aac")
                try:
                    ffmpeg.input(filename=url, f="aac", headers=headers).output(filename=filename).run(
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
        temp_dir_path: Path = self.make_directory(AUDIO_TEMPORARY_DIR_PATH)
        recorded = self._record(temp_dir_path)

        sorted_recorded = sorted(recorded)
        files = [temp_dir_path.joinpath(f"{e}.aac") for e in sorted_recorded]
        logging.debug(files)
        try:
            streams = [ffmpeg.input(filename=f) for f in files]
            ffmpeg.concat(*streams, a=1, v=0).output(filename=self.output_file_path, absf="aac_adtstoasc").run(
                capture_stdout=True
            )
        except Exception as e:
            logging.warning("failed in run ffmpeg concat")
            logging.warning(e)
        finally:
            for f in files:
                os.remove(f)
