from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, Filters

from fa_search_bot.functionalities.functionalities import BotFunctionality
from fa_search_bot.query_parser import InvalidQueryException
from fa_search_bot.subscription_watcher import SubscriptionWatcher, Subscription


class SubscriptionFunctionality(BotFunctionality):
    add_sub_cmd = "add_subscription"
    remove_sub_cmd = "remove_subscription"
    list_sub_cmd = "list_subscriptions"

    def __init__(self, watcher: SubscriptionWatcher):
        super().__init__(CommandHandler, command=[self.add_sub_cmd, self.remove_sub_cmd, self.list_sub_cmd])
        self.watcher = watcher

    def call(self, update: Update, context: CallbackContext):
        message_text = None
        destination = None
        if update.message is not None:
            message_text = update.message.text
            destination = update.message.chat_id
        if update.channel_post is not None:
            message_text = update.channel_post.text
            destination = update.channel_post.chat_id
        if message_text is None or destination is None:
            return None
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
        else:
            context.bot.send_message(
                chat_id=destination,
                text="I do not understand."
            )

    def _add_sub(self, destination: int, query: str):
        if query == "":
            return f"Please specify the subscription query you wish to add."
        try:
            new_sub = Subscription(query, destination)
        except InvalidQueryException as e:
            # TODO: log me
            return f"Failed to parse subscription query: {e}"
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
        subs.sort(key=lambda sub: sub.query_str)
        subs_list = "\n".join([f"- {sub.query_str}" for sub in subs])
        return f"Current active subscriptions in this chat:\n{subs_list}"


class ChannelSubscriptionFunctionality(SubscriptionFunctionality):

    def __init__(self, watcher: SubscriptionWatcher):
        super().__init__(watcher)
        self.handler_cls = MessageHandler
        self.kwargs = {
            "filters": Filters.regex("^/({}|{}|{})".format(self.add_sub_cmd, self.remove_sub_cmd, self.list_sub_cmd))
        }

    def call(self, update: Update, context: CallbackContext):
        if update.channel_post is None:
            return
        if (
                update.channel_post.text.startswith("/" + self.add_sub_cmd)
                or update.channel_post.text.startswith("/" + self.remove_sub_cmd)
                or update.channel_post.text.startswith("/" + self.list_sub_cmd)
        ):
            return super(ChannelSubscriptionFunctionality, self).call(update, context)


class BlocklistFunctionality(BotFunctionality):
    add_block_tag_cmd = "add_blocklisted_tag"
    remove_block_tag_cmd = "remove_blocklisted_tag"
    list_block_tag_cmd = "list_blocklisted_tags"

    def __init__(self, watcher: SubscriptionWatcher):
        super().__init__(
            CommandHandler, command=[self.add_block_tag_cmd, self.remove_block_tag_cmd, self.list_block_tag_cmd]
        )
        self.watcher = watcher

    def call(self, update: Update, context: CallbackContext):
        message_text = None
        destination = None
        if update.message is not None:
            message_text = update.message.text
            destination = update.message.chat_id
        if update.channel_post is not None:
            message_text = update.channel_post.text
            destination = update.channel_post.chat_id
        if message_text is None or destination is None:
            return None
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


class ChannelBlocklistFunctionality(BlocklistFunctionality):

    def __init__(self, watcher: SubscriptionWatcher):
        super().__init__(watcher)
        self.handler_cls = MessageHandler
        self.kwargs = {
            "filters": Filters.regex("^/({}|{}|{})".format(
                self.add_block_tag_cmd, self.remove_block_tag_cmd, self.list_block_tag_cmd
            ))
        }

    def call(self, update: Update, context: CallbackContext):
        if update.channel_post is None:
            return
        if (
                update.channel_post.text.startswith("/" + self.add_block_tag_cmd)
                or update.channel_post.text.startswith("/" + self.remove_block_tag_cmd)
                or update.channel_post.text.startswith("/" + self.list_block_tag_cmd)
        ):
            return super(ChannelBlocklistFunctionality, self).call(update, context)
