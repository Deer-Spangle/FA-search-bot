from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from functionalities.functionalities import BotFunctionality
from subscription_watcher import SubscriptionWatcher, Subscription


class SubscriptionFunctionality(BotFunctionality):

    def __init__(self, watcher: SubscriptionWatcher):
        super().__init__(CommandHandler, command=['add_subscription', 'remove_subscription', 'list_subscriptions'])
        self.watcher = watcher

    def call(self, update: Update, context: CallbackContext):
        message_text = update.message.text
        command = message_text.split()[0]
        args = message_text[len(command):].strip()
        destination = update.message.chat_id
        if command.startswith("/add_subscription"):
            context.bot.send_message(
                chat_id=destination,
                text=self._add_sub(destination, args)
            )
        elif command.startswith("/remove_subscription"):
            context.bot.send_message(
                chat_id=destination,
                text=self._remove_sub(destination, args)
            )
        elif command.startswith("/list_subscriptions"):
            context.bot.send_message(
                chat_id=destination,
                text=self._list_subs(destination)
            )
        else:
            context.bot.send_message(
                chat_id=destination,
                text="I do not understand."
            )

    def _add_sub(self, destination: int, query: str):
        if query == "":
            return f"Please specify the subscription query you wish to add."
        new_sub = Subscription(query, destination)
        self.watcher.subscriptions.add(new_sub)
        return f"Added subscription: \"{query}\".\n{self._list_subs(destination)}"

    def _remove_sub(self, destination: int, query: str):
        old_sub = Subscription(query, destination)
        try:
            self.watcher.subscriptions.remove(old_sub)
            return f"Removed subscription: \"{query}\".\n{self._list_subs(destination)}"
        except KeyError:
            return f"There is not a subscription for \"{query}\" in this chat."

    def _list_subs(self, destination: int):
        subs = [sub for sub in self.watcher.subscriptions if sub.destination == destination]
        subs.sort(key=lambda sub: sub.query)
        subs_list = "\n".join([f"- {sub.query}" for sub in subs])
        return f"Current active subscriptions in this chat:\n{subs_list}"


class BlocklistFunctionality(BotFunctionality):

    def __init__(self, watcher: SubscriptionWatcher):
        super().__init__(
            CommandHandler, command=['add_blocklisted_tag', 'remove_blocklisted_tag', 'list_blocklisted_tags']
        )
        self.watcher = watcher

    def call(self, update: Update, context: CallbackContext):
        message_text = update.message.text
        command = message_text.split()[0]
        args = message_text[len(command):].strip()
        destination = update.message.chat_id
        if command == "/add_blocklisted_tag":
            context.bot.send_message(
                chat_id=destination,
                text=self._add_to_blocklist(destination, args)
            )
        elif command == "/remove_blocklisted_tag":
            context.bot.send_message(
                chat_id=destination,
                text=self._remove_from_blocklist(destination, args)
            )
        elif command == "/list_blocklisted_tags":
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
        self.watcher.add_to_blocklist(destination, query)
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
