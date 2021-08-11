import logging

from telethon.events import NewMessage, StopPropagation

from fa_search_bot.functionalities.functionalities import BotFunctionality

logger = logging.getLogger(__name__)


class UnhandledMessageFunctionality(BotFunctionality):

    def __init__(self):
        super().__init__(NewMessage(incoming=True))

    async def call(self, event: NewMessage.Event):
        if event.text is not None and event.is_private:
            logger.info("Unhandled message sent to bot")
            self.usage_counter.inc()
            await event.reply(
                "Sorry, I'm not sure how to handle that message",
            )
            raise StopPropagation
