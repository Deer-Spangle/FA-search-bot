import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

from fa_search_bot.bot import FASearchBot


def setup_logging() -> None:
    os.makedirs("fa_search_bot/logs", exist_ok=True)
    formatter = logging.Formatter("{asctime}:{levelname}:{name}:{message}", style="{")

    base_logger = logging.getLogger()
    base_logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    base_logger.addHandler(console_handler)

    # FA search bot log, for diagnosing the bot. Should not contain user information.
    fa_logger = logging.getLogger("fa_search_bot")
    file_handler = TimedRotatingFileHandler("fa_search_bot/logs/fa_search_bot.log", when="midnight")
    file_handler.setFormatter(formatter)
    fa_logger.addHandler(file_handler)

    # Set up feature usage logger. Anonymous information on how often features are used
    usage_logger = logging.getLogger("usage")
    usage_logger.setLevel(logging.DEBUG)
    usage_file = logging.FileHandler("fa_search_bot/logs/usage.log")
    usage_file.setFormatter(formatter)
    usage_logger.addHandler(usage_file)


if __name__ == "__main__":
    setup_logging()
    bot = FASearchBot(os.getenv('CONFIG_FILE', 'fa_search_bot/config.json'))
    bot.start()
