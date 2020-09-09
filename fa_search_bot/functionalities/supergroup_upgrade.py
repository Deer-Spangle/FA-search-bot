import logging

import telegram
from telegram import Chat
from telegram.ext import MessageHandler, CallbackContext, Filters

from fa_search_bot.functionalities.functionalities import BotFunctionality
from fa_search_bot.subscription_watcher import SubscriptionWatcher

usage_logger = logging.getLogger("usage")
logger = logging.getLogger(__name__)


class SupergroupUpgradeFunctionality(BotFunctionality):

    def __init__(self, watcher: SubscriptionWatcher):
        super().__init__(MessageHandler, filters=Filters.status_update.migrate)
        self.watcher = watcher

    def call(self, update: telegram.Update, context: CallbackContext):
        old_chat_id = update.message.migrate_from_chat_id
        new_chat_id = update.message.migrate_to_chat_id
        # Only one of these is set, so the other is the chat id
        if old_chat_id is None:
            old_chat_id = update.message.chat_id
        if new_chat_id is None:
            new_chat_id = update.message.chat_id
        # Log the upgrade
        logger.info("Migration from chat ID: %s to chat ID: %s", old_chat_id, new_chat_id)
        usage_logger.info("Supergroup migration")
        # Upgrade subscriptions and block queries
        self.watcher.migrate_chat(old_chat_id, new_chat_id)
