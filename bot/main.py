"""
Main loop: every CHECK_INTERVAL_SECONDS during market hours, fetch fresh
candles, evaluate the strategy, and send a Telegram message if a new signal
fires. Designed to run as a long-lived process on Railway (worker service).
"""

import logging
import time
from datetime import datetime

from . import config
from .instruments import get_current_crudeoil_instrument_key
from .notifier import format_signal_message, send_telegram_message, format_expiry_for_display
from .strategy import evaluate
from .upstox_client import UpstoxClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")


def is_market_open(now: datetime | None = None) -> bool:
    now = now or datetime.now()
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    open_t = now.replace(
        hour=config.MARKET_OPEN_HOUR, minute=config.MARKET_OPEN_MINUTE, second=0, microsecond=0
    )
    close_t = now.replace(
        hour=config.MARKET_CLOSE_HOUR, minute=config.MARKET_CLOSE_MINUTE, second=0, microsecond=0
    )
    return open_t <= now <= close_t


def run():
    logger.info("Starting Crude Oil Signal Bot...")
    client = UpstoxClient(config.UPSTOX_ACCESS_TOKEN)

    instrument_key, instrument_info = get_current_crudeoil_instrument_key()
    expiry_display = format_expiry_for_display(instrument_info.get("expiry"))
    logger.info("Tracking instrument: %s", instrument_key)

    last_signal_direction = None
    last_signal_time = None

    while True:
        try:
            if not is_market_open():
                logger.info("Market closed. Sleeping...")
                time.sleep(config.CHECK_INTERVAL_SECONDS)
                continue

            raw_candles = client.get_intraday_candles(
                instrument_key, config.CANDLE_INTERVAL_MINUTES
            )
            signal = evaluate(raw_candles)

            if signal is not None:
                now = datetime.now()
                same_direction_recent = (
                    last_signal_direction == signal.direction
                    and last_signal_time is not None
                    and (now - last_signal_time).total_seconds()
                    < config.MIN_MINUTES_BETWEEN_SAME_SIGNAL * 60
                )

                if same_direction_recent:
                    logger.info(
                        "Same-direction signal (%s) suppressed -- last one was %.1f min ago.",
                        signal.direction,
                        (now - last_signal_time).total_seconds() / 60,
                    )
                else:
                    message = format_signal_message(signal, expiry_display)
                    send_telegram_message(message)
                    last_signal_direction = signal.direction
                    last_signal_time = now
            else:
                logger.info("No signal this cycle.")

        except Exception as e:
            logger.exception("Error during signal check cycle: %s", e)
            # Don't crash the whole process on a transient API hiccup --
            # log it and try again next cycle.

        time.sleep(config.CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
