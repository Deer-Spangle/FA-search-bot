import html
import logging
import re

from telethon.events import NewMessage, StopPropagation

from fa_search_bot.functionalities.functionalities import BotFunctionality
from fa_search_bot.query_parser import InvalidQueryException
from fa_search_bot.subscription_watcher import SubscriptionWatcher, Subscription

logger = logging.getLogger(__name__)


class SubscriptionFunctionality(BotFunctionality):
    add_sub_cmd = "add_subscription"
    remove_sub_cmd = "remove_subscription"
    list_sub_cmd = "list_subscriptions"
    pause_cmds = ["pause", "suspend"]
    resume_cmds = ["unpause", "resume"]
    USE_CASE_ADD = "add subscription"
    USE_CASE_REMOVE = "remove subscription"
    USE_CASE_LIST = "list subscriptions"
    USE_CASE_PAUSE_DEST = "pause destination"
    USE_CASE_PAUSE_SUB = "pause subscription"
    USE_CASE_RESUME_DEST = "resume destination"
    USE_CASE_RESUME_SUB = "resume subscription"

    def __init__(self, watcher: SubscriptionWatcher):
        commands = [self.add_sub_cmd, self.remove_sub_cmd, self.list_sub_cmd] + self.pause_cmds + self.resume_cmds
        commands_pattern = re.compile(r"^/(" + "|".join(re.escape(c) for c in commands) + ")")
        super().__init__(NewMessage(pattern=commands_pattern, incoming=True))
        self.watcher = watcher
        self.usage_counter.labels(use_case=self.USE_CASE_ADD)
        self.usage_counter.labels(use_case=self.USE_CASE_REMOVE)
        self.usage_counter.labels(use_case=self.USE_CASE_LIST)
        self.usage_counter.labels(use_case=self.USE_CASE_PAUSE_DEST)
        self.usage_counter.labels(use_case=self.USE_CASE_PAUSE_SUB)
        self.usage_counter.labels(use_case=self.USE_CASE_RESUME_DEST)
        self.usage_counter.labels(use_case=self.USE_CASE_RESUME_SUB)

    async def call(self, event: NewMessage.Event):
        message_text = event.text
        command = message_text.split()[0]
        args = message_text[len(command):].strip()
        await event.reply(
            self._route_command(event.chat_id, command, args),
            parse_mode='html'
        )
        raise StopPropagation

    def _route_command(self, destination: int, command: str, args: str) -> str:
        if command.startswith("/" + self.add_sub_cmd):
            return self._add_sub(destination, args)
        elif command.startswith("/" + self.remove_sub_cmd):
            return self._remove_sub(destination, args)
        elif command.startswith("/" + self.list_sub_cmd):
            return self._list_subs(destination)
        elif any(command.startswith("/" + cmd) for cmd in self.pause_cmds):
            if args:
                return self._pause_subscription(destination, args)
            return self._pause_destination(destination)
        elif any(command.startswith("/" + cmd) for cmd in self.resume_cmds):
            if args:
                return self._resume_subscription(destination, args)
            return self._resume_destination(destination)
        else:
            return "I do not understand."

    def _add_sub(self, destination: int, query: str):
        self.usage_counter.labels(use_case=self.USE_CASE_ADD).inc()
        if query == "":
            return f"Please specify the subscription query you wish to add."
        try:
            new_sub = Subscription(query, destination)
        except InvalidQueryException as e:
            logger.error("Failed to parse new subscription query: %s", query, exc_info=e)
            return f"Failed to parse subscription query: {html.escape(str(e))}"
        if new_sub in self.watcher.subscriptions:
            return f"A subscription already exists for \"{html.escape(query)}\"."
        self.watcher.subscriptions.add(new_sub)
        return f"Added subscription: \"{html.escape(query)}\".\n{self._list_subs(destination)}"

    def _remove_sub(self, destination: int, query: str):
        self.usage_counter.labels(use_case=self.USE_CASE_REMOVE).inc()
        old_sub = Subscription(query, destination)
        try:
            self.watcher.subscriptions.remove(old_sub)
            return f"Removed subscription: \"{html.escape(query)}\".\n{self._list_subs(destination)}"
        except KeyError:
            return f"There is not a subscription for \"{html.escape(query)}\" in this chat."

    def _list_subs(self, destination: int):
        self.usage_counter.labels(use_case=self.USE_CASE_LIST).inc()
        subs = [sub for sub in self.watcher.subscriptions if sub.destination == destination]
        subs.sort(key=lambda sub: sub.query_str.casefold())
        sub_list_entries = []
        for sub in subs:
            sub_title = f"- {html.escape(sub.query_str)}"
            if sub.paused:
                sub_title = f"- ⏸<s>{html.escape(sub.query_str)}</s>"
            sub_list_entries.append(sub_title)
        subs_list = "\n".join(sub_list_entries)
        return f"Current subscriptions in this chat:\n{subs_list}"

    def _pause_destination(self, chat_id: int):
        self.usage_counter.labels(use_case=self.USE_CASE_PAUSE_DEST).inc()
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
        self.usage_counter.labels(use_case=self.USE_CASE_PAUSE_SUB).inc()
        pause_sub = Subscription(sub_name, chat_id)
        if pause_sub not in self.watcher.subscriptions:
            return f"There is not a subscription for \"{html.escape(sub_name)}\" in this chat."
        matching = [sub for sub in self.watcher.subscriptions if sub == pause_sub][0]
        if matching.paused:
            return f"Subscription for \"{html.escape(sub_name)}\" is already paused."
        matching.paused = True
        return f"Paused subscription: \"{html.escape(sub_name)}\".\n{self._list_subs(chat_id)}"

    def _resume_destination(self, chat_id: int) -> str:
        self.usage_counter.labels(use_case=self.USE_CASE_RESUME_DEST).inc()
        subs = [sub for sub in self.watcher.subscriptions if sub.destination == chat_id]
        if not subs:
            return "There are no subscriptions posting here to resume."
        running_subs = [sub for sub in subs if sub.paused is True]
        if not running_subs:
            return "All subscriptions are already running."
        for sub in running_subs:
            sub.paused = False
        return f"Resumed all subscriptions.\n{self._list_subs(chat_id)}"

    def _resume_subscription(self, chat_id: int, sub_name: str) -> str:
        self.usage_counter.labels(use_case=self.USE_CASE_RESUME_SUB).inc()
        pause_sub = Subscription(sub_name, chat_id)
        if pause_sub not in self.watcher.subscriptions:
            return f"There is not a subscription for \"{html.escape(sub_name)}\" in this chat."
        matching = [sub for sub in self.watcher.subscriptions if sub == pause_sub][0]
        if not matching.paused:
            return f"Subscription for \"{html.escape(sub_name)}\" is already running."
        matching.paused = False
        return f"Resumed subscription: \"{html.escape(sub_name)}\".\n{self._list_subs(chat_id)}"


class BlocklistFunctionality(BotFunctionality):
    add_block_tag_cmd = "add_blocklisted_tag"
    remove_block_tag_cmd = "remove_blocklisted_tag"
    list_block_tag_cmd = "list_blocklisted_tags"
    USE_CASE_ADD = "add block"
    USE_CASE_REMOVE = "remove block"
    USE_CASE_LIST = "list blocks"

    def __init__(self, watcher: SubscriptionWatcher):
        commands = [self.add_block_tag_cmd, self.remove_block_tag_cmd, self.list_block_tag_cmd]
        commands_pattern = re.compile(r"^/(" + "|".join(re.escape(c) for c in commands) + ")")
        super().__init__(NewMessage(pattern=commands_pattern, incoming=True))
        self.watcher = watcher
        self.usage_counter.labels(use_case=self.USE_CASE_ADD)
        self.usage_counter.labels(use_case=self.USE_CASE_REMOVE)
        self.usage_counter.labels(use_case=self.USE_CASE_LIST)

    async def call(self, event: NewMessage.Event):
        message_text = event.text
        destination = event.chat_id
        command = message_text.split()[0]
        args = message_text[len(command):].strip()
        if command.startswith("/" + self.add_block_tag_cmd):
            await event.reply(
                self._add_to_blocklist(destination, args)
            )
        elif command.startswith("/" + self.remove_block_tag_cmd):
            await event.reply(
                self._remove_from_blocklist(destination, args)
            )
        elif command.startswith("/" + self.list_block_tag_cmd):
            await event.reply(
                self._list_blocklisted_tags(destination)
            )
        else:
            await event.reply(
                "I do not understand."
            )
        raise StopPropagation

    def _add_to_blocklist(self, destination: int, query: str):
        self.usage_counter.labels(use_case=self.USE_CASE_ADD).inc()
        if query == "":
            return f"Please specify the tag you wish to add to blocklist."
        try:
            self.watcher.add_to_blocklist(destination, query)
        except InvalidQueryException as e:
            return f"Failed to parse blocklist query: {e}"
        return f"Added tag to blocklist: \"{query}\".\n{self._list_blocklisted_tags(destination)}"

    def _remove_from_blocklist(self, destination: int, query: str):
        self.usage_counter.labels(use_case=self.USE_CASE_REMOVE).inc()
        try:
            self.watcher.blocklists.get(destination, []).remove(query)
            return f"Removed tag from blocklist: \"{query}\".\n{self._list_blocklisted_tags(destination)}"
        except KeyError:
            return f"The tag \"{query}\" is not on the blocklist for this chat."

    def _list_blocklisted_tags(self, destination: int):
        self.usage_counter.labels(use_case=self.USE_CASE_LIST).inc()
        blocklist = self.watcher.blocklists.get(destination, [])
        tags_list = "\n".join([f"- {tag}" for tag in blocklist])
        return f"Current blocklist for this chat:\n{tags_list}"
