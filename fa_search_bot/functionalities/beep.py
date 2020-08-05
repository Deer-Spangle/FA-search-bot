import logging

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from fa_search_bot.functionalities.functionalities import BotFunctionality

usage_logger = logging.getLogger("usage")
logger = logging.getLogger("fa_search_bot.functionalities.beep")


class BeepFunctionality(BotFunctionality):

    def __init__(self):
        super().__init__(CommandHandler, command='beep')

    def call(self, update: Update, context: CallbackContext):
        logger.info("Beep")
        usage_logger.info("Beep function")
        context.bot.send_message(chat_id=update.message.chat_id, text="boop")
