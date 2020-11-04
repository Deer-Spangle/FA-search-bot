from telegram import Update
from telegram.ext import CallbackContext

from fa_search_bot.functionalities.channel_agnostic_func import ChannelAgnosticFunctionality
from fa_search_bot.subscription_watcher import SubscriptionWatcher


class SubPauseFunctionality(ChannelAgnosticFunctionality):

    def __init__(self, watcher: SubscriptionWatcher):
        super().__init__(["pause", "suspend"])
        self.watcher = watcher

    def call_text(self, update: Update, context: CallbackContext, text: str, chat_id: int):
        pass

    def _pause_destination(self, chat_id: int):
        pass

    def _pause_subscription(self, chat_id: int, sub_name: str):
        pass


class SubResumeFunctionality(ChannelAgnosticFunctionality):

    def __init__(self, watcher: SubscriptionWatcher):
        super().__init__(["unpause", "resume"])
        self.watcher = watcher

    def call_text(self, update: Update, context: CallbackContext, text: str, chat_id: int):
        pass

    def _resume_destination(self, chat_id: int):
        pass

    def _resume_subscription(self, chat_id: int, sub_name: str):
        pass
