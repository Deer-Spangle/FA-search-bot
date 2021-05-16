import logging

from telethon.events import NewMessage, StopPropagation

from fa_search_bot.functionalities.functionalities import BotFunctionality

usage_logger = logging.getLogger("usage")
logger = logging.getLogger(__name__)


class UnhandledMessageFunctionality(BotFunctionality):

    def __init__(self):
        super().__init__(NewMessage())

    async def call(self, event: NewMessage.Event):
        if event.message is not None and event.is_private:
            logger.info("Unhandled message sent to bot")
            usage_logger.info("Unhandled message")
            await event.reply(
                "Sorry, I'm not sure how to handle that message",
            )
            raise StopPropagation
