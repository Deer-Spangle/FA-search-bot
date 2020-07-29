from fa_search_bot.functionalities.subscriptions import ChannelBlocklistFunctionality
from fa_search_bot.subscription_watcher import SubscriptionWatcher
from fa_search_bot.tests.util.mock_export_api import MockExportAPI
from fa_search_bot.tests.util.mock_method import MockMethod
from fa_search_bot.tests.util.mock_telegram_update import MockTelegramUpdate


def test_call__route_add_blocklisted_tag(context):
    update = MockTelegramUpdate.with_channel_post(chat_id=-10014358, text="/add_blocklisted_tag test")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = ChannelBlocklistFunctionality(watcher)
    add_tag = MockMethod("Added to channel blocklist: test")
    func._add_to_blocklist = add_tag.call

    func.call(update, context)

    assert add_tag.called
    assert add_tag.args is not None
    assert add_tag.args[0] == -10014358
    assert add_tag.args[1] == "test"
    context.bot.send_message.assert_called()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.channel_post.chat_id
    assert context.bot.send_message.call_args[1]['text'] == "Added to channel blocklist: test"


def test_call__route_remove_blocklisted_tag(context):
    update = MockTelegramUpdate.with_channel_post(chat_id=-10014358, text="/remove_blocklisted_tag example")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = ChannelBlocklistFunctionality(watcher)
    remove_tag = MockMethod("Removed from channel blocklist: example")
    func._remove_from_blocklist = remove_tag.call

    func.call(update, context)

    assert remove_tag.called
    assert remove_tag.args is not None
    assert remove_tag.args[0] == -10014358
    assert remove_tag.args[1] == "example"
    context.bot.send_message.assert_called()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.channel_post.chat_id
    assert context.bot.send_message.call_args[1]['text'] == "Removed from channel blocklist: example"


def test_call__route_list_blocklisted_tags(context):
    update = MockTelegramUpdate.with_channel_post(chat_id=-10014358, text="/list_blocklisted_tags")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = ChannelBlocklistFunctionality(watcher)
    list_tags = MockMethod("Listing channel blocklisted tags")
    func._list_blocklisted_tags = list_tags.call

    func.call(update, context)

    assert list_tags.called
    assert list_tags.args is not None
    assert list_tags.args[0] == -10014358
    context.bot.send_message.assert_called()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.channel_post.chat_id
    assert context.bot.send_message.call_args[1]['text'] == "Listing channel blocklisted tags"
