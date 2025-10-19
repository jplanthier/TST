from __future__ import annotations


def _ema(series: pd.Series, length: int) -> pd.Series:
return series.ewm(span=length, adjust=False).mean()


def _rsi(series: pd.Series, length: int = 14) -> pd.Series:
delta = series.diff()
up = delta.clip(lower=0)
down = -delta.clip(upper=0)
roll_up = up.rolling(length).mean()
roll_down = down.rolling(length).mean()
rs = roll_up / (roll_down + 1e-12)
return 100 - (100 / (1 + rs))


def _macd(series: pd.Series, fast=12, slow=26, signal=9):
ema_fast = _ema(series, fast)
ema_slow = _ema(series, slow)
macd = ema_fast - ema_slow
sig = macd.ewm(span=signal, adjust=False).mean()
hist = macd - sig
return macd, sig, hist


# --- Public API ---


def compute_indicators(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
close = df["close"]
out = df.copy()


ema_cfg = cfg["indicators"]["ema"]
rsi_cfg = cfg["indicators"]["rsi"]
macd_cfg = cfg["indicators"]["macd"]


# EMA
if ema_cfg.get("enabled", True):
if ta:
out["ema_fast"] = ta.ema(close, length=int(ema_cfg.get("fast", 20)))
out["ema_mid"] = ta.ema(close, length=int(ema_cfg.get("mid", 50)))
out["ema_slow"] = ta.ema(close, length=int(ema_cfg.get("slow", 200)))
else:
out["ema_fast"] = _ema(close, int(ema_cfg.get("fast", 20)))
out["ema_mid"] = _ema(close, int(ema_cfg.get("mid", 50)))
out["ema_slow"] = _ema(close, int(ema_cfg.get("slow", 200)))


# RSI
if rsi_cfg.get("enabled", True):
if ta:
out["rsi"] = ta.rsi(close, length=int(rsi_cfg.get("length", 14)))
else:
out["rsi"] = _rsi(close, int(rsi_cfg.get("length", 14)))


# MACD
if macd_cfg.get("enabled", True):
f = int(macd_cfg.get("fast", 12))
s = int(macd_cfg.get("slow", 26))
sig = int(macd_cfg.get("signal", 9))
if ta:
macd = ta.macd(close, fast=f, slow=s, signal=sig)
out["macd"] = macd["MACD_12_26_9"].rename("macd") if "MACD_12_26_9" in macd else macd.iloc[:,0]
out["macd_signal"] = macd["MACDs_12_26_9"].rename("macd_signal") if "MACDs_12_26_9" in macd else macd.iloc[:,1]
out["macd_hist"] = macd["MACDh_12_26_9"].rename("macd_hist") if "MACDh_12_26_9" in macd else macd.iloc[:,2]
else:
m, s_, h = _macd(close, fast=f, slow=s, signal=sig)
out["macd"], out["macd_signal"], out["macd_hist"] = m, s_, h


return out
