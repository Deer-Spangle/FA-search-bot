import logging

from telethon.events import NewMessage, StopPropagation

from fa_search_bot.filters import filter_image_no_caption
from fa_search_bot.functionalities.functionalities import BotFunctionality

usage_logger = logging.getLogger("usage")
logger = logging.getLogger(__name__)


class ImageHashRecommendFunctionality(BotFunctionality):

    def __init__(self):
        events = NewMessage(func=filter_image_no_caption)
        super().__init__(events)

    async def call(self, event: NewMessage.Event):
        if event.is_private:
            usage_logger.info("Image hash recommend")
            logger.info("Recommending image hash bots")
            await event.reply(
                "I can't find an image without a link, try using @FindFurryPicBot or @FoxBot. "
                "For gifs, try @reverseSearchBot."
            )
            raise StopPropagation
