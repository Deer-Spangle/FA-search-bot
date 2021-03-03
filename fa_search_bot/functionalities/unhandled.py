import logging

import telegram
from telegram import Chat
from telegram.ext import MessageHandler, CallbackContext, Filters

from fa_search_bot.functionalities.functionalities import BotFunctionality

usage_logger = logging.getLogger("usage")
logger = logging.getLogger(__name__)


class UnhandledMessageFunctionality(BotFunctionality):

    def __init__(self):
        super().__init__(MessageHandler, filters=Filters.all)

    def call(self, update: telegram.Update, context: CallbackContext):
        if update.message is not None and update.message.chat.type == Chat.PRIVATE:
            logger.info("Unhandled message sent to bot")
            usage_logger.info("Unhandled message")
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="Sorry, I'm not sure how to handle that message",
                reply_to_message_id=update.message.message_id
            )
