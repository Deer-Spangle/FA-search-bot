import datetime

from unittest.mock import patch
import telegram

from fa_search_bot.functionalities.sub_pause import SubResumeFunctionality
from fa_search_bot.functionalities.subscriptions import SubscriptionFunctionality
from fa_search_bot.subscription_watcher import SubscriptionWatcher, Subscription
from fa_search_bot.tests.util.mock_export_api import MockExportAPI
from fa_search_bot.tests.util.mock_method import MockMethod
from fa_search_bot.tests.util.mock_telegram_update import MockTelegramUpdate


@patch.object(telegram, "Bot")
def test_call__route_resume_destination(context):
    update = MockTelegramUpdate.with_message(chat_id=14358, text="/resume")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = SubResumeFunctionality(watcher)
    resume_dest = MockMethod("Resumed all subscriptions")
    func._resume_destination = resume_dest.call

    func.call(update, context)

    assert resume_dest.called
    assert resume_dest.args is not None
    assert resume_dest.args[0] == update.message.chat_id
    context.bot.send_message.assert_called()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_message.call_args[1]['text'] == "Resumed all subscriptions"


@patch.object(telegram, "Bot")
def test_call__route_unpause_destination(context):
    update = MockTelegramUpdate.with_message(chat_id=14358, text="/unpause")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = SubResumeFunctionality(watcher)
    resume_dest = MockMethod("Resumed all subscriptions")
    func._resume_destination = resume_dest.call

    func.call(update, context)

    assert resume_dest.called
    assert resume_dest.args is not None
    assert resume_dest.args[0] == update.message.chat_id
    context.bot.send_message.assert_called()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_message.call_args[1]['text'] == "Resumed all subscriptions"


@patch.object(telegram, "Bot")
def test_call__route_resume_destination_with_handle(context):
    update = MockTelegramUpdate.with_message(chat_id=14358, text="/resume@FASearchBot")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = SubResumeFunctionality(watcher)
    resume_dest = MockMethod("Resumed all subscriptions")
    func._resume_destination = resume_dest.call

    func.call(update, context)

    assert resume_dest.called
    assert resume_dest.args is not None
    assert resume_dest.args[0] == update.message.chat_id
    context.bot.send_message.assert_called()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_message.call_args[1]['text'] == "Resumed all subscriptions"


@patch.object(telegram, "Bot")
def test_call__route_resume_subscription(context):
    update = MockTelegramUpdate.with_message(chat_id=14358, text="/resume test")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = SubResumeFunctionality(watcher)
    resume_sub = MockMethod("Resumed subscription")
    func._resume_subscription = resume_sub.call

    func.call(update, context)

    assert resume_sub.called
    assert resume_sub.args is not None
    assert resume_sub.args[0] == update.message.chat_id
    assert resume_sub.args[1] == "test"
    context.bot.send_message.assert_called()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_message.call_args[1]['text'] == "Resumed subscription"


@patch.object(telegram, "Bot")
def test_call__route_resume_subscription_with_handle(context):
    update = MockTelegramUpdate.with_message(chat_id=14358, text="/resume@FASearchBot test")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = SubResumeFunctionality(watcher)
    resume_sub = MockMethod("Resumed subscription")
    func._resume_subscription = resume_sub.call

    func.call(update, context)

    assert resume_sub.called
    assert resume_sub.args is not None
    assert resume_sub.args[0] == update.message.chat_id
    assert resume_sub.args[1] == "test"
    context.bot.send_message.assert_called()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_message.call_args[1]['text'] == "Resumed subscription"


@patch.object(telegram, "Bot")
def test_resume_destination__no_subs(context):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = SubResumeFunctionality(watcher)

    resp = func._resume_destination(18749)

    assert resp == "There are no subscriptions posting here to resume."
    assert len(watcher.subscriptions) == 0


@patch.object(telegram, "Bot")
def test_resume_destination__one_sub(context):
    assert False
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    resp = func._add_sub(18749, "test")

    assert "Added subscription" in resp
    assert "\"test\"" in resp
    assert list_subs.called
    assert list_subs.args[0] == 18749
    assert "Listing subscriptions" in resp
    assert len(watcher.subscriptions) == 1
    subscription = list(watcher.subscriptions)[0]
    assert subscription.query_str == "test"
    assert subscription.destination == 18749
    assert subscription.latest_update is None


@patch.object(telegram, "Bot")
def test_resume_destination__multiple_subs(context):
    assert False
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    watcher.subscriptions.add(Subscription("example", 18749))
    watcher.subscriptions.add(Subscription("test", 18747))
    func = SubscriptionFunctionality(watcher)

    resp = func._remove_sub(18749, "test")

    assert resp == "There is not a subscription for \"test\" in this chat."
    assert len(watcher.subscriptions) == 2


@patch.object(telegram, "Bot")
def test_resume_destination__all_running(context):
    assert False


@patch.object(telegram, "Bot")
def test_resume_subscription__no_matching(context):
    assert False
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    watcher.subscriptions.add(Subscription("example", 18749))
    watcher.subscriptions.add(Subscription("test", 18747))
    new_sub = Subscription("test", 18749)
    new_sub.latest_update = datetime.datetime.now()
    watcher.subscriptions.add(new_sub)
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    resp = func._remove_sub(18749, "test")

    assert "Removed subscription: \"test\"." in resp
    assert list_subs.called
    assert list_subs.args[0] == 18749
    assert "Listing subscriptions" in resp
    assert len(watcher.subscriptions) == 2
    subscriptions = list(watcher.subscriptions)
    if subscriptions[0].query_str == "test":
        assert subscriptions[0].destination == 18747
        assert subscriptions[1].query_str == "example"
        assert subscriptions[1].destination == 18749
    else:
        assert subscriptions[0].query_str == "example"
        assert subscriptions[0].destination == 18749
        assert subscriptions[1].query_str == "test"
        assert subscriptions[1].destination == 18747


@patch.object(telegram, "Bot")
def test_resume_subscription__one_matching(context):
    assert False
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    watcher.subscriptions.add(Subscription("example", 18749))
    watcher.subscriptions.add(Subscription("test", 18747))
    watcher.subscriptions.add(Subscription("deer", 18749))
    func = SubscriptionFunctionality(watcher)

    resp = func._list_subs(18749)

    assert "Current active subscriptions in this chat:" in resp
    assert "- deer" in resp
    assert "- example" in resp
    assert "- test" not in resp


@patch.object(telegram, "Bot")
def test_resume_subscription__case_insensitive(context):
    assert False
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    watcher.subscriptions.add(Subscription("example", 18749))
    watcher.subscriptions.add(Subscription("test", 18749))
    watcher.subscriptions.add(Subscription("deer", 18749))
    func = SubscriptionFunctionality(watcher)

    resp = func._list_subs(18749)

    assert "Current active subscriptions in this chat:" in resp
    assert "- deer\n- example\n- test" in resp


@patch.object(telegram, "Bot")
def test_resume_subscription__already_running(context):
    assert False
