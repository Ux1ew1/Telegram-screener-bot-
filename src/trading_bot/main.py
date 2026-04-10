from __future__ import annotations

import logging
import sys

from .app import TradingBotApp
from .config import load_settings


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    configure_logging()
    settings = load_settings()

    if not settings.telegram_bot_token:
        print("Missing TELEGRAM_BOT_TOKEN in .env", file=sys.stderr)
        return 1

    app = TradingBotApp(settings).build()
    app.run_polling(drop_pending_updates=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
