import os

from dotenv import load_dotenv

load_dotenv(verbose=True)

AUDIO_OUTPUT_DIR_PATH = os.getenv("AUDIO_OUTPUT_DIR_PATH", "./work/output")
AUDIO_TEMPORARY_DIR_PATH = os.getenv("AUDIO_TEMPORARY_DIR_PATH", "./work/output/.tmp")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "./work/log/app.log")
RADIKO_AREA_ID = os.getenv("RADIKO_AREA_ID", "JP14")
S3_BUCKET = os.getenv("S3_BUCKET", "radiko-bucket")
