import logging

import telegram
from telegram import Chat
from telegram.ext import MessageHandler, CallbackContext

from fa_search_bot.filters import FilterImageNoCaption
from fa_search_bot.functionalities.functionalities import BotFunctionality

usage_logger = logging.getLogger("usage")
logger = logging.getLogger(__name__)


class ImageHashRecommendFunctionality(BotFunctionality):

    def __init__(self):
        super().__init__(MessageHandler, filters=FilterImageNoCaption())

    def call(self, update: telegram.Update, context: CallbackContext):
        logger.info("Recommending image hash bots")
        usage_logger.info("Image hash recommend")
        if update.message.chat.type == Chat.PRIVATE:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="I can't find an image without a link, try using @FindFurryPicBot or @FoxBot",
                reply_to_message_id=update.message.message_id
            )
