import logging
from typing import List

from telethon.events import NewMessage, StopPropagation

from fa_search_bot.filters import filter_image_no_caption
from fa_search_bot.functionalities.functionalities import BotFunctionality

logger = logging.getLogger(__name__)


class ImageHashRecommendFunctionality(BotFunctionality):
    def __init__(self) -> None:
        events = NewMessage(func=filter_image_no_caption, incoming=True)
        super().__init__(events)

    async def call(self, event: NewMessage.Event) -> None:
        if event.is_private:
            self.usage_counter.labels(function="image_hash_recommend").inc()
            logger.info("Recommending image hash bots")
            await event.reply(
                "I can't find an image without a link, try using @FindFurryPicBot or @FoxBot. "
                "For gifs, try @reverseSearchBot."
            )
            raise StopPropagation

    @property
    def usage_labels(self) -> List[str]:
        return ["image_hash_recommend"]
