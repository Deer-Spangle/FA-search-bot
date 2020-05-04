from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from functionalities.functionalities import BotFunctionality


class BeepFunctionality(BotFunctionality):

    def __init__(self):
        super().__init__(CommandHandler, command='beep')

    def call(self, update: Update, context: CallbackContext):
        context.bot.send_message(chat_id=update.message.chat_id, text="boop")
