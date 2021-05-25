import logging

from telethon import events

from fa_search_bot.functionalities.functionalities import BotFunctionality

usage_logger = logging.getLogger("usage")
logger = logging.getLogger(__name__)


class BeepFunctionality(BotFunctionality):

    def __init__(self):
        super().__init__(events.NewMessage(pattern="/beep", incoming=True))

    async def call(self, event: events.NewMessage.Event) -> None:
        logger.info("Beep")
        usage_logger.info("Beep function")
        await event.respond("boop")
        raise events.StopPropagation
