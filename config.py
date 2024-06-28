import os
import logging
import urllib.parse

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent
LOGS_DIR = ROOT_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

SCHEMAS_DIR = ROOT_DIR / "schema"
SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)

SESSIONS_DIR = ROOT_DIR / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


# LOGGING
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=LOGS_DIR / "stdout.log",
    encoding="utf-8",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# KEYS
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EXTERNAL_SCHEMA_API_ENDPOINT = os.getenv("EXTERNAL_SCHEMA_API_ENDPOINT")
DB_TOOL_API = os.getenv("DB_TOOL_API")

MONGODB_USERNAME = urllib.parse.quote_plus(os.getenv("MONGODB_USERNAME"))
MONGODB_PASSWORD = urllib.parse.quote_plus(os.getenv("MONGODB_PASSWORD"))
MONGODB_HOST = os.getenv("MONGODB_HOST")
MONGODB_PORT = os.getenv("MONGODB_PORT")
MONGODB_DB = os.getenv("MONGODB_DB")
MONDODB_REPLICA_SET_NAME = os.getenv("MONDODB_REPLICA_SET_NAME")

MONGODB_URI = f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}/{MONGODB_DB}?authSource={MONGODB_DB}"
if MONDODB_REPLICA_SET_NAME:
    MONGODB_URI += f"&replicaSet={MONDODB_REPLICA_SET_NAME}"
