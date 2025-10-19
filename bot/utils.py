import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv


# Logging
logging.basicConfig(
level=logging.INFO,
format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("bot")


# Paths
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# Env
load_dotenv()


TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
MODE = os.getenv("MODE", "paper").lower() # 'paper' | 'live'
LIVE_PASSPHRASE = os.getenv("LIVE_PASSPHRASE", "change_me_securely")


BITGET_API_KEY = os.getenv("BITGET_API_KEY", "")
BITGET_API_SECRET = os.getenv("BITGET_API_SECRET", "")
BITGET_PASSPHRASE = os.getenv("BITGET_PASSPHRASE", "")


# Config loader
CONFIG_PATH = Path(__file__).with_name("config.json")


def load_config():
with open(CONFIG_PATH, "r") as f:
return json.load(f)


CONFIG = load_config()


# Helpers


def timeframe_to_seconds(tf: str) -> int:
tf = tf.lower()
if tf in ("1h", "1hr", "1hour"): return 60*60
if tf in ("4h", "4hr", "4hours"): return 4*60*60
if tf in ("1d", "1day", "1d1"): return 24*60*60
raise ValueError(f"Unsupported timeframe: {tf}")




def as_pair(symbol: str) -> str:
s = symbol.upper().replace("/", "")
return s
