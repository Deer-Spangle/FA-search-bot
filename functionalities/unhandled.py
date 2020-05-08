import telegram
from telegram import Chat
from telegram.ext import MessageHandler, CallbackContext, Filters

from functionalities.functionalities import BotFunctionality


class UnhandledMessageFunctionality(BotFunctionality):
    
    def __init__(self):
        super().__init__(MessageHandler, filters=Filters.all)

    def call(self, update: telegram.Update, context: CallbackContext):
        if update.message.chat.type == Chat.PRIVATE:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="Sorry, I'm not sure how to handle that message"
            )
