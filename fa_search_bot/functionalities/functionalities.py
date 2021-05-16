from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Optional

import telegram
from telegram.ext import CallbackContext
from telethon import TelegramClient
from telethon.events.common import EventCommon, EventBuilder


@contextmanager
def in_progress_msg(update: telegram.Update, context: CallbackContext, text: Optional[str]):
    if text is None:
        text = f"In progress"
    text = f"⏳ {text}"
    msg_promise = context.bot.send_message(
        chat_id=update.message.chat_id,
        text=text,
        reply_to_message_id=update.message.message_id
    )
    msg = msg_promise.result()
    try:
        yield
    except Exception as e:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"Command failed. Sorry, I tried but failed to process this.",
            reply_to_message_id=update.message.message_id
        )
        raise e
    finally:
        context.bot.delete_message(update.message.chat_id, msg.message_id)


class BotFunctionality(ABC):

    def __init__(self, event: EventBuilder):
        self.event = event

    def register(self, client: TelegramClient) -> None:
        client.add_event_handler(self.call, self.event)

    @abstractmethod
    async def call(self, event: EventCommon) -> None:
        pass
