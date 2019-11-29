import datetime
import unittest

from unittest.mock import patch
import telegram

from bot import SubscriptionFunctionality
from subscription_watcher import SubscriptionWatcher, Subscription
from tests.util.mock_export_api import MockExportAPI
from tests.util.mock_method import MockMethod
from tests.util.mock_telegram_update import MockTelegramUpdate


class SubscriptionFunctionalityTest(unittest.TestCase):

    @patch.object(telegram, "Bot")
    def test_call__route_add_subscription(self, bot):
        update = MockTelegramUpdate.with_message(chat_id=14358, text="/add_subscription test")
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
        func = SubscriptionFunctionality(watcher)
        add_sub = MockMethod("Added subscription test")
        func._add_sub = add_sub.call

        func.call(bot, update)

        assert add_sub.called
        assert add_sub.args is not None
        assert add_sub.args[0] == 14358
        assert add_sub.args[1] == "test"
        bot.send_message.assert_called()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == "Added subscription test"

    @patch.object(telegram, "Bot")
    def test_call__route_remove_subscription(self, bot):
        update = MockTelegramUpdate.with_message(chat_id=14358, text="/remove_subscription example")
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
        func = SubscriptionFunctionality(watcher)
        delete_sub = MockMethod("Removed subscription test")
        func._remove_sub = delete_sub.call

        func.call(bot, update)

        assert delete_sub.called
        assert delete_sub.args is not None
        assert delete_sub.args[0] == 14358
        assert delete_sub.args[1] == "example"
        bot.send_message.assert_called()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == "Removed subscription test"

    @patch.object(telegram, "Bot")
    def test_call__route_list_subscriptions(self, bot):
        update = MockTelegramUpdate.with_message(chat_id=14358, text="/list_subscriptions")
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
        func = SubscriptionFunctionality(watcher)
        list_subs = MockMethod("Listing subscriptions")
        func._list_subs = list_subs.call

        func.call(bot, update)

        assert list_subs.called
        assert list_subs.args is not None
        assert list_subs.args[0] == 14358
        bot.send_message.assert_called()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == "Listing subscriptions"

    @patch.object(telegram, "Bot")
    def test_add_sub__no_add_blank(self, bot):
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
        func = SubscriptionFunctionality(watcher)

        resp = func._add_sub(18749, "")

        assert resp == "Please specify the subscription query you wish to add."
        assert len(watcher.subscriptions) == 0

    @patch.object(telegram, "Bot")
    def test_add_sub__adds_subscription(self, bot):
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
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
        assert subscription.query == "test"
        assert subscription.destination == 18749
        assert subscription.latest_update is None

    @patch.object(telegram, "Bot")
    def test_remove_sub__non_existent_subscription(self, bot):
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
        watcher.subscriptions.add(Subscription("example", 18749))
        watcher.subscriptions.add(Subscription("test", 18747))
        func = SubscriptionFunctionality(watcher)

        resp = func._remove_sub(18749, "test")

        assert resp == "There is not a subscription for \"test\" in this chat."
        assert len(watcher.subscriptions) == 2

    @patch.object(telegram, "Bot")
    def test_remove_sub__removes_subscription(self, bot):
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
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
        if subscriptions[0].query == "test":
            assert subscriptions[0].destination == 18747
            assert subscriptions[1].query == "example"
            assert subscriptions[1].destination == 18749
        else:
            assert subscriptions[0].query == "example"
            assert subscriptions[0].destination == 18749
            assert subscriptions[1].query == "test"
            assert subscriptions[1].destination == 18747

    @patch.object(telegram, "Bot")
    def test_list_subs(self, bot):
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
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
    def test_list_subs__alphabetical(self, bot):
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
        watcher.subscriptions.add(Subscription("example", 18749))
        watcher.subscriptions.add(Subscription("test", 18749))
        watcher.subscriptions.add(Subscription("deer", 18749))
        func = SubscriptionFunctionality(watcher)

        resp = func._list_subs(18749)

        assert "Current active subscriptions in this chat:" in resp
        assert "- deer\n- example\n- test" in resp
