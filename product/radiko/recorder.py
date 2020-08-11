import logging
import os
from pathlib import Path

import boto3
import ffmpeg
from directory_mixin import DirectoryMixin
from settings import AUDIO_TEMPORARY_DIR_PATH

from .downloader import Downloader


class RadikoRecorder(DirectoryMixin):
    def __init__(self, station: str, record_time: int, output_file_path: Path, s3_bucket: str) -> None:
        self.station = station
        self.record_time = record_time
        self.output_file_path = output_file_path
        self.s3_bucket = s3_bucket

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

        s3 = boto3.resource("s3")
        bucket = s3.Bucket(self.s3_bucket)
        bucket.upload_file(str(self.output_file_path), self.output_file_path.name)  # ファイルはバケット直下にアップロードする
