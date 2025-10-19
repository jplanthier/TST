from __future__ import annotations
import time
import httpx
import pandas as pd
from typing import List
from .utils import logger, timeframe_to_seconds, as_pair


BASE = "https://api.bitget.com"


# Public candles endpoint (spot). For futures later you can switch to /mix endpoints.
# Docs may evolve; we use a conservative approach and parse flexibly.
CANDLES_EP = "/api/v2/spot/market/candles"


TIMEOUT = 20.0


async def fetch_candles(symbol: str, timeframe: str, limit: int = 300) -> pd.DataFrame:
"""Fetch OHLCV candles and return a DataFrame sorted by time ascending.
Columns: ts (int, ms), open, high, low, close, volume (float)
"""
gran = timeframe_to_seconds(timeframe)


params = {
"symbol": as_pair(symbol), # e.g. BTCUSDT
"granularity": gran, # seconds per candle
"limit": min(limit, 1000),
}


async with httpx.AsyncClient(timeout=TIMEOUT) as client:
r = await client.get(BASE + CANDLES_EP, params=params)
r.raise_for_status()
data = r.json()


# Expected format: { "data": [[ts, open, high, low, close, volume], ...] } (often newest first)
raw = data.get("data") or data
if not isinstance(raw, list):
raise RuntimeError(f"Unexpected candles payload: {data}")


# Normalize rows to floats
rows: List[dict] = []
for row in raw:
# many exchanges return newest first; make robust checks
ts = int(row[0])
o, h, l, c, v = map(float, row[1:6])
rows.append({"ts": ts, "open": o, "high": h, "low": l, "close": c, "volume": v})


df = pd.DataFrame(rows).sort_values("ts").reset_index(drop=True)


# Bitget often returns ts in ms. If it looks like seconds, convert to ms for consistency
if df["ts"].iloc[-1] < 10_000_000_000: # < year ~2286 in seconds
df["ts"] *= 1000


return df


async def fetch_price(symbol: str) -> float:
"""Fetch latest price using last candle close for default timeframe (1h)."""
df = await fetch_candles(symbol, "1h", limit=1)
return float(df["close"].iloc[-1])
