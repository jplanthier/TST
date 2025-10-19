import asyncio
from .utils import TELEGRAM_TOKEN, logger
from .telegram_bot import build_app


def main():
    if not TELEGRAM_TOKEN:
        raise SystemExit("TELEGRAM_TOKEN missing. Set it in your .env")
    app = build_app()
    logger.info("Starting Telegram bot...")
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
