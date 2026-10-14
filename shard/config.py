"""Configuration — paths, settings, env vars."""

import os
from pathlib import Path

DB_PATH = Path(os.environ.get("SHARD_DB", "shard.db"))
DATA_DIR = Path(os.environ.get("SHARD_DATA", "data"))

BATCH_SIZE = 5000
DEDUP_ALGO = "sha256"
MAX_LINE_LEN = 4096
MIN_LINE_LEN = 5

DEFAULT_LIMIT = 50
MAX_LIMIT = 500

APP_NAME = "shard"
APP_VERSION = "0.1.0"
