from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from telethon.events import NewMessage, StopPropagation

from fa_search_bot.functionalities.functionalities import BotFunctionality

if TYPE_CHECKING:
    from typing import List

logger = logging.getLogger(__name__)


class UnhandledMessageFunctionality(BotFunctionality):
    def __init__(self) -> None:
        super().__init__(NewMessage(incoming=True))

    @property
    def usage_labels(self) -> List[str]:
        return ["unhandled"]

    async def call(self, event: NewMessage.Event) -> None:
        if event.text is not None and event.is_private:
            logger.info("Unhandled message sent to bot")
            self.usage_counter.labels(function="unhandled").inc()
            await event.reply(
                "Sorry, I'm not sure how to handle that message",
            )
            raise StopPropagation
