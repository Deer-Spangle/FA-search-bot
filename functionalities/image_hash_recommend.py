import telegram
from telegram import Chat
from telegram.ext import MessageHandler

from filters import FilterImageNoCaption
from functionalities.functionalities import BotFunctionality


class ImageHashRecommendFunctionality(BotFunctionality):

    def __init__(self):
        super().__init__(MessageHandler, filters=FilterImageNoCaption())

    def call(self, bot, update: telegram.Update):
        if update.message.chat.type == Chat.PRIVATE:
            bot.send_message(
                chat_id=update.message.chat_id,
                text="I can't find an image without a link, try using @FindFurryPicBot",
                reply_to_message_id=update.message.message_id
            )
