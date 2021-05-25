import logging

from telethon.events import NewMessage, StopPropagation
from telethon.extensions import markdown

from fa_search_bot._version import __VERSION__
from fa_search_bot.functionalities.functionalities import BotFunctionality

usage_logger = logging.getLogger("usage")
logger = logging.getLogger(__name__)


class WelcomeFunctionality(BotFunctionality):

    def __init__(self):
        super().__init__(NewMessage(pattern='/start', incoming=True))

    async def call(self, event: NewMessage.Event):
        logger.info("Welcome message sent to user")
        usage_logger.info("Welcome message")
        await event.respond(
            "Hello, I'm a bot to interface with furaffinity through telegram. I can do a few things, "
            "but there's still more for me to learn.\n"
            "If you have any suggestions, requests, or questions, direct them to @deerspangle, "
            "or you can file an issue on my [github](https://github.com/Deer-Spangle/FA-search-bot).\n"
            f"I am version {__VERSION__} and currently I can:\n"
            "- Neaten up any FA submission, direct links, and thumbnail links you give me\n"
            "- Optimise FA gif submissions for telegram\n"
            "- Respond to inline search queries (and browse user galleries inline)\n"
            "- Create subscriptions, with specified queries. See readme for more details on query syntax\n"
            "- Store blocklists for those subscriptions\n"
            "You can get more details by reading "
            "[my README on github](https://github.com/Deer-Spangle/FA-search-bot#commands)",
            parse_mode=markdown
        )
        raise StopPropagation
