import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple

from const import Const
from directory_mixin import DirectoryMixin
from settings import AUDIO_OUTPUT_DIR_PATH, LOG_FILE_PATH

from radiko.recorder import RadikoRecorder


class App(DirectoryMixin):
    def __init__(self, station: str, program: str, record_time: int) -> None:
        self.station = station
        self.program = program
        self.record_time = record_time

    def _get_output_file_path(self) -> Path:
        dir_path = self.make_directory(AUDIO_OUTPUT_DIR_PATH)

        current_time = datetime.now(tz=Const.JST).strftime("%Y%m%d-%H%M")
        filename = f"{self.station}_{self.program}_{current_time}.aac"

        return dir_path.joinpath(filename).resolve()

    def boot(self) -> None:
        file_path: Path = self._get_output_file_path()
        logging.debug(f"OUTPUT_FILE_PATH:{file_path}")

        recorder = RadikoRecorder(self.station, self.record_time, file_path)
        recorder.execute()


def _parse_params() -> Tuple[str, str, int]:
    parser = argparse.ArgumentParser()
    parser.add_argument("station", type=str, help="放送局")
    parser.add_argument("program", type=str, help="番組名")
    parser.add_argument("record_time", type=int, help="録音時間")

    args = parser.parse_args()
    return args.station, args.program, args.record_time


if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILE_PATH, level=logging.DEBUG, format="[%(levelname)s]\t%(message)s")

    station, program, record_time = _parse_params()
    app = App(station, program, record_time)
    app.boot()
