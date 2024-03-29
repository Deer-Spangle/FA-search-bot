from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING, Generator

from prometheus_client import Counter
from telethon.events import StopPropagation

if TYPE_CHECKING:
    from typing import AsyncIterator, List, Optional, Tuple

    from telethon import TelegramClient
    from telethon.events import InlineQuery, NewMessage
    from telethon.events.common import EventBuilder, EventCommon

usage_counter = Counter("fasearchbot_usage_total", "Total usage of bot features", labelnames=["function"])

logger = logging.getLogger(__name__)


@asynccontextmanager
async def in_progress_msg(event: NewMessage.Event, text: Optional[str]) -> AsyncIterator[None]:
    if text is None:
        text = "In progress"
    text = f"⏳ {text}"
    msg = await event.reply(text)
    try:
        yield
    except StopPropagation as e:
        raise e
    except Exception as e:
        logger.error("Unhandled exception in functionality handler", exc_info=e)
        await event.reply("Command failed. Sorry, I tried but failed to process this.")
        raise StopPropagation
    finally:
        await msg.delete()


async def answer_with_error(event: InlineQuery.Event, title: str, msg: str) -> None:
    await event.answer(
        results=[
            await event.builder.article(
                title=title,
                description=msg,
                text=msg,
            )
        ],
        gallery=False,
        next_offset=None,
    )


@contextmanager
def log_inline_exceptions(msg: str) -> Generator[None, None, None]:
    try:
        yield
    except Exception as e:
        if not isinstance(e, StopPropagation):
            logger.error(msg, exc_info=e)
        raise e


class BotFunctionality(ABC):
    def __init__(self, event: EventBuilder):
        self.event = event
        self.usage_counter = usage_counter

    def register(self, client: TelegramClient) -> None:
        client.add_event_handler(self._wrap_call, self.event)

    async def _wrap_call(self, event: EventCommon) -> None:
        try:
            await self.call(event)
        except Exception as e:
            if not isinstance(e, StopPropagation):
                logger.error("Failure when calling %s functionality", self.__class__.__name__, exc_info=e)
            raise e

    @abstractmethod
    async def call(self, event: EventCommon) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def usage_labels(self) -> List[str]:
        raise NotImplementedError


def _parse_inline_offset(offset: str) -> Tuple[int, Optional[int]]:
    if offset == "":
        page, skip = 1, None
    elif ":" in offset:
        page, skip = (int(x) for x in offset.split(":", 1))
    else:
        page, skip = int(offset), None
    return page, skip
