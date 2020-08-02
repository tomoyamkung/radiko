import logging
import os
from pathlib import Path

import ffmpeg
from directory_mixin import DirectoryMixin
from settings import AUDIO_TEMPORARY_DIR_PATH

from .downloader import Downloader


class RadikoRecorder(DirectoryMixin):
    def __init__(self, station: str, record_time: int, output_file_path: Path) -> None:
        self.station = station
        self.record_time = record_time
        self.output_file_path = output_file_path

    def execute(self):
        filepaths = Downloader.execute(self.station, self.record_time, self.make_directory(AUDIO_TEMPORARY_DIR_PATH))
        try:
            streams = [ffmpeg.input(filename=path) for path in filepaths]
            ffmpeg.concat(*streams, a=1, v=0).output(filename=self.output_file_path, absf="aac_adtstoasc").run(
                capture_stdout=True
            )
        except Exception as e:
            logging.warning("failed in run ffmpeg concat")
            logging.warning(e)
        finally:
            for f in filepaths:
                os.remove(f)
