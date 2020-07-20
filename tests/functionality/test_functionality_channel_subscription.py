from unittest.mock import patch

import telegram

from functionalities.subscriptions import ChannelSubscriptionFunctionality
from subscription_watcher import SubscriptionWatcher
from tests.util.mock_export_api import MockExportAPI
from tests.util.mock_method import MockMethod
from tests.util.mock_telegram_update import MockTelegramUpdate


@patch.object(telegram, "Bot")
def test_call__route_add_subscription(context):
    update = MockTelegramUpdate.with_channel_post(chat_id=-10014358, text="/add_subscription test")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = ChannelSubscriptionFunctionality(watcher)
    add_sub = MockMethod("Added channel subscription test")
    func._add_sub = add_sub.call

    func.call(update, context)

    assert add_sub.called
    assert add_sub.args is not None
    assert add_sub.args[0] == -10014358
    assert add_sub.args[1] == "test"
    context.bot.send_message.assert_called()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.channel_post.chat_id
    assert context.bot.send_message.call_args[1]['text'] == "Added channel subscription test"


@patch.object(telegram, "Bot")
def test_call__route_remove_subscription(context):
    update = MockTelegramUpdate.with_channel_post(chat_id=-10014358, text="/remove_subscription example")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = ChannelSubscriptionFunctionality(watcher)
    delete_sub = MockMethod("Removed channel subscription test")
    func._remove_sub = delete_sub.call

    func.call(update, context)

    assert delete_sub.called
    assert delete_sub.args is not None
    assert delete_sub.args[0] == -10014358
    assert delete_sub.args[1] == "example"
    context.bot.send_message.assert_called()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.channel_post.chat_id
    assert context.bot.send_message.call_args[1]['text'] == "Removed channel subscription test"


@patch.object(telegram, "Bot")
def test_call__route_list_subscriptions(context):
    update = MockTelegramUpdate.with_channel_post(chat_id=-10014358, text="/list_subscriptions")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = ChannelSubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing channel subscriptions")
    func._list_subs = list_subs.call

    func.call(update, context)

    assert list_subs.called
    assert list_subs.args is not None
    assert list_subs.args[0] == -10014358
    context.bot.send_message.assert_called()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.channel_post.chat_id
    assert context.bot.send_message.call_args[1]['text'] == "Listing channel subscriptions"
