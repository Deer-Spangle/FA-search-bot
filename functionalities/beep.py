from telegram.ext import CommandHandler

from functionalities.functionalities import BotFunctionality


class BeepFunctionality(BotFunctionality):

    def __init__(self):
        super().__init__(CommandHandler, command='beep')

    def call(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="boop")