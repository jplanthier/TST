from __future__ import annotations
import pandas as pd
from typing import Literal, Tuple

Signal = Literal["BUY", "SELL", "NEUTRAL"]


def macd_cross(now_macd: float, now_sig: float, prev_macd: float, prev_sig: float) -> int:
    """Return +1 for bullish cross, -1 for bearish cross, 0 otherwise."""
    if prev_macd < prev_sig and now_macd > now_sig:
        return +1
    if prev_macd > prev_sig and now_macd < now_sig:
        return -1
    return 0


def evaluate(df: pd.DataFrame) -> Tuple[Signal, dict]:
    """Apply simple swing logic on the last two candles of df (with indicators)."""
    assert len(df) >= 2, "Need at least 2 candles"
    last = df.iloc[-1]
    prev = df.iloc[-2]

    price = float(last["close"])  # current close

    ema50 = float(last.get("ema_mid", float("nan")))
    rsi = float(last.get("rsi", float("nan")))
    macd = float(last.get("macd", float("nan")))
    macd_sig = float(last.get("macd_signal", float("nan")))
    macd_prev = float(prev.get("macd", float("nan")))
    macd_sig_prev = float(prev.get("macd_signal", float("nan")))

    cross = macd_cross(macd, macd_sig, macd_prev, macd_sig_prev)

    ema_trend_bull = price > ema50
    ema_trend_bear = price < ema50
    macd_bull = cross == +1 or macd > macd_sig
    macd_bear = cross == -1 or macd < macd_sig

    # Core rules
    buy = ema_trend_bull and (rsi < 70) and macd_bull
    sell = ema_trend_bear and (rsi > 30) and macd_bear

    # Confidence (simple heuristic 0..100)
    conf = 50
    conf += 20 if ema_trend_bull or ema_trend_bear else 0
    conf += 15 if cross != 0 else 0
    conf += 10 if (30 <= rsi <= 70) else 0
    conf = max(0, min(100, conf))

    details = {
        "price": price,
        "ema50": ema50,
        "ema_trend": "Bullish" if ema_trend_bull else ("Bearish" if ema_trend_bear else "Sideways"),
        "rsi": round(rsi, 2) if pd.notna(rsi) else None,
        "macd_comment": "Bullish crossover" if cross == +1 else ("Bearish crossover" if cross == -1 else ("Above signal" if macd > macd_sig else "Below signal")),
        "confidence": conf,
    }

    if buy:
        return "BUY", details
    if sell:
        return "SELL", details
    return "NEUTRAL", details
