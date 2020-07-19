import telegram
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from _version import __VERSION__
from functionalities.functionalities import BotFunctionality


class WelcomeFunctionality(BotFunctionality):

    def __init__(self):
        super().__init__(CommandHandler, command='start')

    def call(self, update: Update, context: CallbackContext):
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Hello, I'm a bot to interface with furaffinity through telegram. I can do a few things, "
                 "but there's still more for me to learn.\n"
                 "If you have any suggestions, requests, or questions, direct them to @deerspangle, "
                 "or you can file an issue on my [github](https://github.com/Deer-Spangle/FA-search-bot).\n"
                 f"I am version {__VERSION__} and currently I can:\n"
                 "- Neaten up any FA submission, direct links, and thumbnail links you give me\n"
                 "- Respond to inline search queries (and browse user galleries inline)\n"
                 "- Create subscriptions, with specified queries. See readme for more details on query syntax\n"
                 "- Store blocklists for those subscriptions\n"
                 "You can get more details by reading "
                 "[my README on github](https://github.com/Deer-Spangle/FA-search-bot#commands)",
            parse_mode=telegram.ParseMode.MARKDOWN
        )