import logging

from telegram import Update
from telegram.ext import CallbackContext

from fa_search_bot.functionalities.channel_agnostic_func import ChannelAgnosticFunctionality
from fa_search_bot.query_parser import InvalidQueryException
from fa_search_bot.subscription_watcher import SubscriptionWatcher, Subscription

usage_logger = logging.getLogger("usage")
logger = logging.getLogger(__name__)


class SubscriptionFunctionality(ChannelAgnosticFunctionality):
    add_sub_cmd = "add_subscription"
    remove_sub_cmd = "remove_subscription"
    list_sub_cmd = "list_subscriptions"
    pause_cmds = ["pause", "suspend"]
    resume_cmds = ["unpause", "resume"]

    def __init__(self, watcher: SubscriptionWatcher):
        commands = [self.add_sub_cmd, self.remove_sub_cmd, self.list_sub_cmd] + self.pause_cmds + self.resume_cmds
        super().__init__(commands)
        self.watcher = watcher

    def call_text(self, update: Update, context: CallbackContext, text: str, chat_id: int):
        message_text = text
        destination = chat_id
        command = message_text.split()[0]
        args = message_text[len(command):].strip()
        if command.startswith("/" + self.add_sub_cmd):
            context.bot.send_message(
                chat_id=destination,
                text=self._add_sub(destination, args)
            )
        elif command.startswith("/" + self.remove_sub_cmd):
            context.bot.send_message(
                chat_id=destination,
                text=self._remove_sub(destination, args)
            )
        elif command.startswith("/" + self.list_sub_cmd):
            context.bot.send_message(
                chat_id=destination,
                text=self._list_subs(destination)
            )
        elif any(command.startswith("/" + cmd) for cmd in self.pause_cmds):
            if args:
                return context.bot.send_message(
                    chat_id=chat_id,
                    text=self._pause_subscription(chat_id, args)
                )
            context.bot.send_message(
                chat_id=chat_id,
                text=self._pause_destination(chat_id)
            )
        elif any(command.startswith("/" + cmd) for cmd in self.resume_cmds):
            if args:
                return context.bot.send_message(
                    chat_id=chat_id,
                    text=self._resume_subscription(chat_id, args)
                )
            context.bot.send_message(
                chat_id=chat_id,
                text=self._resume_destination(chat_id)
            )
        else:
            context.bot.send_message(
                chat_id=destination,
                text="I do not understand."
            )

    def _add_sub(self, destination: int, query: str):
        usage_logger.info("Add subscription")
        if query == "":
            return f"Please specify the subscription query you wish to add."
        try:
            new_sub = Subscription(query, destination)
        except InvalidQueryException as e:
            logger.error("Failed to parse new subscription query: %s", query, exc_info=e)
            return f"Failed to parse subscription query: {e}"
        if new_sub in self.watcher.subscriptions:
            return f"A subscription already exists for \"{query}\"."
        self.watcher.subscriptions.add(new_sub)
        return f"Added subscription: \"{query}\".\n{self._list_subs(destination)}"

    def _remove_sub(self, destination: int, query: str):
        usage_logger.info("Remove subscription")
        old_sub = Subscription(query, destination)
        try:
            self.watcher.subscriptions.remove(old_sub)
            return f"Removed subscription: \"{query}\".\n{self._list_subs(destination)}"
        except KeyError:
            return f"There is not a subscription for \"{query}\" in this chat."

    def _list_subs(self, destination: int):
        usage_logger.info("List subscriptions")
        subs = [sub for sub in self.watcher.subscriptions if sub.destination == destination]
        subs.sort(key=lambda sub: sub.query_str.casefold())
        subs_list = "\n".join([f"- {'⏸' if sub.paused else ''}{sub.query_str}" for sub in subs])
        return f"Current active subscriptions in this chat:\n{subs_list}"

    def _pause_destination(self, chat_id: int):
        usage_logger.info("Pause destination")
        subs = [sub for sub in self.watcher.subscriptions if sub.destination == chat_id]
        if not subs:
            return "There are no subscriptions posting here to pause."
        running_subs = [sub for sub in subs if sub.paused is False]
        if not running_subs:
            return "All subscriptions are already paused."
        for sub in running_subs:
            sub.paused = True
        return f"Paused all subscriptions.\n{self._list_subs(chat_id)}"

    def _pause_subscription(self, chat_id: int, sub_name: str):
        usage_logger.info("Pause subscription")
        pause_sub = Subscription(sub_name, chat_id)
        if pause_sub not in self.watcher.subscriptions:
            return f"There is not a subscription for \"{sub_name}\" in this chat."
        matching = [sub for sub in self.watcher.subscriptions if sub == pause_sub][0]
        if matching.paused:
            return f"Subscription for \"{sub_name}\" is already paused."
        matching.paused = True
        return f"Paused subscription \"{sub_name}\".\n{self._list_subs(chat_id)}"

    def _resume_destination(self, chat_id: int) -> str:
        pass

    def _resume_subscription(self, chat_id: int, sub_name: str) -> str:
        pass


class BlocklistFunctionality(ChannelAgnosticFunctionality):
    add_block_tag_cmd = "add_blocklisted_tag"
    remove_block_tag_cmd = "remove_blocklisted_tag"
    list_block_tag_cmd = "list_blocklisted_tags"

    def __init__(self, watcher: SubscriptionWatcher):
        super().__init__([self.add_block_tag_cmd, self.remove_block_tag_cmd, self.list_block_tag_cmd])
        self.watcher = watcher

    def call_text(self, update: Update, context: CallbackContext, text: str, chat_id: int):
        message_text = text
        destination = chat_id
        command = message_text.split()[0]
        args = message_text[len(command):].strip()
        if command.startswith("/" + self.add_block_tag_cmd):
            context.bot.send_message(
                chat_id=destination,
                text=self._add_to_blocklist(destination, args)
            )
        elif command.startswith("/" + self.remove_block_tag_cmd):
            context.bot.send_message(
                chat_id=destination,
                text=self._remove_from_blocklist(destination, args)
            )
        elif command.startswith("/" + self.list_block_tag_cmd):
            context.bot.send_message(
                chat_id=destination,
                text=self._list_blocklisted_tags(destination)
            )
        else:
            context.bot.send_message(
                chat_id=destination,
                text="I do not understand."
            )

    def _add_to_blocklist(self, destination: int, query: str):
        if query == "":
            return f"Please specify the tag you wish to add to blocklist."
        try:
            self.watcher.add_to_blocklist(destination, query)
        except InvalidQueryException as e:
            return f"Failed to parse blocklist query: {e}"
        return f"Added tag to blocklist: \"{query}\".\n{self._list_blocklisted_tags(destination)}"

    def _remove_from_blocklist(self, destination: int, query: str):
        try:
            self.watcher.blocklists[destination].remove(query)
            return f"Removed tag from blocklist: \"{query}\".\n{self._list_blocklisted_tags(destination)}"
        except KeyError:
            return f"The tag \"{query}\" is not on the blocklist for this chat."

    def _list_blocklisted_tags(self, destination: int):
        blocklist = self.watcher.blocklists[destination]
        tags_list = "\n".join([f"- {tag}" for tag in blocklist])
        return f"Current blocklist for this chat:\n{tags_list}"
