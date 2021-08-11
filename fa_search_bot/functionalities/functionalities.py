from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Optional

from prometheus_client import Counter
from telethon import TelegramClient
from telethon.events import NewMessage, StopPropagation
from telethon.events.common import EventCommon, EventBuilder


@asynccontextmanager
async def in_progress_msg(event: NewMessage.Event, text: Optional[str]):
    if text is None:
        text = f"In progress"
    text = f"⏳ {text}"
    msg = await event.reply(text)
    try:
        yield
    except Exception:
        await event.reply(
            "Command failed. Sorry, I tried but failed to process this."
        )
        raise StopPropagation
    finally:
        await msg.delete()


class BotFunctionality(ABC):

    def __init__(self, event: EventBuilder):
        self.event = event
        self.usage_counter = Counter(
            "fasearchbot_usage_total",
            "Total usage of bot features"
        ).labels(function_class=self.__class__.__name__)

    def register(self, client: TelegramClient) -> None:
        client.add_event_handler(self.call, self.event)

    @abstractmethod
    async def call(self, event: EventCommon) -> None:
        raise NotImplementedError
