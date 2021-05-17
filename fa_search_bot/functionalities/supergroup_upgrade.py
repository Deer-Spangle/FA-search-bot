import logging

from telethon import events
from telethon.events import StopPropagation
from telethon.tl import types
from telethon.tl.types import UpdateNewChannelMessage

from fa_search_bot.functionalities.functionalities import BotFunctionality
from fa_search_bot.subscription_watcher import SubscriptionWatcher

usage_logger = logging.getLogger("usage")
logger = logging.getLogger(__name__)


def filter_migration(event: UpdateNewChannelMessage) -> bool:
    if event.message and event.message.action is not None:
        return isinstance(event.message.action, types.MessageActionChannelMigrateFrom)
    return False


class SupergroupUpgradeFunctionality(BotFunctionality):

    def __init__(self, watcher: SubscriptionWatcher):
        super().__init__(events.Raw(types.UpdateNewChannelMessage, func=filter_migration))
        self.watcher = watcher

    def call(self, event: types.UpdateNewChannelMessage):
        old_chat_id = -1 * event.message.action.chat_id
        new_chat_id = int('-100' + str(event.message.to_id.channel_id))
        # Log the upgrade
        logger.info("Migration from chat ID: %s to chat ID: %s", old_chat_id, new_chat_id)
        usage_logger.info("Supergroup migration")
        # Upgrade subscriptions and block queries
        self.watcher.migrate_chat(old_chat_id, new_chat_id)
        raise StopPropagation
