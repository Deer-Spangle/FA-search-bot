from abc import abstractmethod
from typing import List

import telegram
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, Filters, MessageHandler

from fa_search_bot.functionalities.functionalities import BotFunctionality


class ChannelAgnosticFunctionality(BotFunctionality):

    def __init__(self, commands: List[str]):
        super().__init__(
            MessageHandler,
            filters=Filters.regex("^/("+"|".join(commands)+")")
        )

    def call(self, update: telegram.Update, context: CallbackContext):
        message_text = None
        destination = None
        if update.message is not None:
            message_text = update.message.text
            destination = update.message.chat_id
        if update.channel_post is not None:
            message_text = update.channel_post.text
            destination = update.channel_post.chat_id
        if message_text is None or destination is None:
            return None
        return self.call_text(update, context, message_text, destination)

    @abstractmethod
    def call_text(self, update: Update, context: CallbackContext, text: str, chat_id: int):
        pass
