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
                 "If you have any suggestions, requests, or questions, direct them to @deerspangle.\n"
                 f"I am version {__VERSION__} and currently I can:\n"
                 "- Neaten up any FA submission, direct links, and thumbnail links you give me\n"
                 "- Respond to inline search queries\n"
                 "- Browse user galleries, scraps and favourites inline "
                 "(use the format 'gallery:username', 'scraps:username', or 'favs:username')\n"
                 "- Create subscriptions "
                 "(use `/add_subscription query`, `/list_subscriptions` and `/remove_subscription query`)\n"
                 "- Store blacklists for those subscriptions "
                 "(use `/add_blacklisted_tag tag`, `/list_blacklisted_tags` and `/remove_blacklisted_tag tag`)"
        )