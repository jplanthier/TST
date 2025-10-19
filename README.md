# TST
# Bitget Swing Bot (Beginner‑Friendly)


A Telegram bot that fetches BTC/USDT candles from Bitget, computes basic indicators (EMA, RSI, MACD), and generates swing trade signals. Starts in **paper mode** with a virtual balance, with a safe path to upgrade to **live futures** later.


## Features (MVP)
- Public OHLCV from Bitget (1h / 4h / 1D)
- Indicators: EMA(20/50/200), RSI(14), MACD(12,26,9)
- Simple swing logic → Buy / Sell / Neutral + Confidence
- Paper trading with SQLite persistence
- Telegram commands to control the bot
- Configurable via `bot/config.json` or inline commands


## Quickstart
1. **Clone & Install**
```bash
python -m venv .venv && source .venv/bin/activate # (Windows: .venv\\Scripts\\activate)
pip install -r requirements.txt
