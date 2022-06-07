import logging
from typing import List

from telethon import events

from fa_search_bot.functionalities.functionalities import BotFunctionality

logger = logging.getLogger(__name__)


class BeepFunctionality(BotFunctionality):
    def __init__(self) -> None:
        super().__init__(events.NewMessage(pattern="/beep", incoming=True))

    async def call(self, event: events.NewMessage.Event) -> None:
        logger.info("Beep")
        self.usage_counter.labels(function="beep").inc()
        await event.respond("boop")
        raise events.StopPropagation

    @property
    def usage_labels(self) -> List[str]:
        return ["beep"]
