from __future__ import annotations
import asyncio
from typing import Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .utils import TELEGRAM_TOKEN, MODE, LIVE_PASSPHRASE, CONFIG, logger
from .bitget_api import fetch_candles, fetch_price
from .indicators import compute_indicators
from .signal_engine import evaluate
from .paper_trader import PaperTrader

STATE = {
    "mode": MODE,  # paper | live
    "auto_job": None,
    "symbol": CONFIG.get("default_symbol", "BTCUSDT"),
    "timeframe": CONFIG.get("default_timeframe", "4h"),
}

TRADER = PaperTrader(
    starting_balance=CONFIG["paper"]["starting_balance"],
    risk_pct=CONFIG["paper"]["risk_per_trade_pct"],
)

async def _build_signal(symbol: str, timeframe: str):
    df = await fetch_candles(symbol, timeframe, limit=300)
    df = compute_indicators(df, CONFIG)
    sig, details = evaluate(df.dropna())
    msg = (
        f"📊 Pair: {symbol}\n"
        f"⏱ Timeframe: {timeframe}\n"
        f"💡 Signal: {sig}\n"
        f"EMA Trend: {details['ema_trend']}\n"
        f"RSI: {details['rsi']}\n"
        f"MACD: {details['macd_comment']}\n"
        f"Confidence: {details['confidence']}%\n"
        f"Last Price: {details['price']:.2f}"
    )
    return sig, msg, details

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Bitget Swing Bot!\n"
        f"Mode: {STATE['mode'].upper()}\n"
        f"Default: {STATE['symbol']} {STATE['timeframe']}\n"
        "Type /help for commands."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start\n/price\n/signal\n/auto_on [minutes]\n/auto_off\n/set_mode paper|live\n/set_indicators [key=value ...]\n/balance\n"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await fetch_price(STATE["symbol"])
    await update.message.reply_text(f"{STATE['symbol']} ≈ {p:.2f}")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sig, msg, _ = await _build_signal(STATE["symbol"], STATE["timeframe"])
    await update.message.reply_text(msg)

async def auto_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    try:
        _, msg, _ = await _build_signal(STATE["symbol"], STATE["timeframe"])
        await context.bot.send_message(chat_id, msg)
    except Exception as e:
        logger.exception("auto_job error: %s", e)

async def auto_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    minutes = int(context.args[0]) if context.args else CONFIG.get("auto_interval_minutes", 30)
    if STATE["auto_job"]:
        STATE["auto_job"].schedule_removal()
    job = context.job_queue.run_repeating(auto_job, interval=minutes*60, first=0, chat_id=update.effective_chat.id)
    STATE["auto_job"] = job
    await update.message.reply_text(f"Auto signals ON every {minutes} minutes.")

async def auto_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if STATE["auto_job"]:
        STATE["auto_job"].schedule_removal()
        STATE["auto_job"] = None
    await update.message.reply_text("Auto signals OFF.")

async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text(f"Current mode: {STATE['mode']}")
    mode = context.args[0].lower()
    if mode == "paper":
        STATE["mode"] = "paper"
        return await update.message.reply_text("Switched to PAPER mode.")
    if mode == "live":
        if len(context.args) < 2:
            return await update.message.reply_text("Provide passphrase: /set_mode live <passphrase>")
        if context.args[1] != LIVE_PASSPHRASE:
            return await update.message.reply_text("❌ Wrong passphrase. Staying in paper mode.")
        STATE["mode"] = "live"
        return await update.message.reply_text("⚠️ LIVE mode enabled. Trade functions remain reduce‑only by default.")
    await update.message.reply_text("Unknown mode. Use paper|live.")

async def set_indicators(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text(f"Current: {CONFIG['indicators']}")
    # Example: /set_indicators ema.fast=21 rsi.length=10 macd.enabled=false
    changed = []
    for arg in context.args:
        if "=" not in arg:
            continue
        key, val = arg.split("=", 1)
        path = key.split(".")
        try:
            target = CONFIG
            for p in path[:-1]:
                target = target[p]
            leaf = path[-1]
            # Try parse bool/int/float
            if val.lower() in ("true", "false"):
                v = val.lower() == "true"
            else:
                try:
                    v = int(val)
                except ValueError:
                    try:
                        v = float(val)
                    except ValueError:
                        v = val
            target[leaf] = v
            changed.append(key)
        except Exception:
            pass
    await update.message.reply_text("Updated: " + ", ".join(changed))

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cash = TRADER.get_cash()
    open_positions = TRADER.get_open_positions()
    if not open_positions:
        await update.message.reply_text(f"Paper cash: ${cash:.2f}\nOpen positions: none")
    else:
        lines = [f"Paper cash: ${cash:.2f}", "Open positions:"]
        for p in open_positions:
            lines.append(f"#{p.id} {p.side} {p.qty:.6f} {p.symbol} @ {p.entry:.2f}")
        await update.message.reply_text("\n".join(lines))

# --- Future live trading stubs (disabled) ---
async def _place_live_order(symbol: str, side: str, qty: float):
    raise NotImplementedError("Live trading not yet enabled. This is a safe stub.")


def build_app() -> Application:
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("auto_on", auto_on))
    app.add_handler(CommandHandler("auto_off", auto_off))
    app.add_handler(CommandHandler("set_mode", set_mode))
    app.add_handler(CommandHandler("set_indicators", set_indicators))
    app.add_handler(CommandHandler("balance", balance))

    return app
