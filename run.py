import asyncio
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

import click
from prometheus_client import Counter

from fa_search_bot.bot import FASearchBot
from fa_search_bot.config import Config

log_entries = Counter(
    "fasearchbot_log_messages_total",
    "Number of log messages by logger and level",
    labelnames=["logger", "level"]
)


class LogMetricsHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        log_entries.labels(logger=record.name, level=record.levelname).inc()


def setup_logging(log_level: str = "INFO") -> None:
    os.makedirs("logs", exist_ok=True)
    formatter = logging.Formatter("{asctime}:{levelname}:{name}:{message}", style="{")

    base_logger = logging.getLogger()
    base_logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    base_logger.addHandler(console_handler)

    # FA search bot log, for diagnosing the bot. Should not contain user information.
    fa_logger = logging.getLogger("fa_search_bot")
    file_handler = TimedRotatingFileHandler("logs/fa_search_bot.log", when="midnight")
    file_handler.setFormatter(formatter)
    fa_logger.addHandler(file_handler)
    fa_logger.setLevel(log_level.upper())
    fa_logger.addHandler(LogMetricsHandler())


@click.command()
@click.option("--log-level", type=str, help="Log level for the logger", default="INFO")
@click.option("--no-subscriptions", type=bool, default=False, help="Disable subscription watcher")
@click.option("--sub-watcher-data-fetchers", type=int, default=2, help="Number of DataFetcher tasks which should spin up in the subscription watcher")
@click.option("--sub-watcher-media-fetchers", type=int, default=2, help="Number of MediaFetcher tasks which should spin up in the subscription watcher")
def main(
        log_level: str,
        no_subscriptions: bool,
        sub_watcher_data_fetchers: int,
        sub_watcher_media_fetchers: int,
) -> None:
    setup_logging(log_level)
    # Construct config and ingest flags
    config = Config.load_from_file(os.getenv('CONFIG_FILE', 'config.json'))
    config.subscription_watcher.enabled = not no_subscriptions
    config.subscription_watcher.num_data_fetchers = not sub_watcher_data_fetchers
    config.subscription_watcher.num_media_fetchers = not sub_watcher_media_fetchers
    # Create and start the bot
    bot = FASearchBot(config)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.run())


if __name__ == "__main__":
    main()
