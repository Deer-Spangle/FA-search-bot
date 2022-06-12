import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

from prometheus_client import Counter

from fa_search_bot.bot import FASearchBot, Config

log_entries = Counter(
    "fasearchbot_log_messages_total",
    "Number of log messages by logger and level",
    labelnames=["logger", "level"]
)


class LogMetricsHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        log_entries.labels(logger=record.name, level=record.levelname).inc()


def setup_logging() -> None:
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
    fa_logger.addHandler(LogMetricsHandler())


if __name__ == "__main__":
    setup_logging()
    config = Config.load_from_file(os.getenv('CONFIG_FILE', 'config.json'))
    bot = FASearchBot(config)
    bot.start()
    bot.run()
