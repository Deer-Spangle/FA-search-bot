import unittest

from unittest.mock import patch
import telegram

from bot import BlacklistFunctionality
from subscription_watcher import SubscriptionWatcher
from tests.util.mock_export_api import MockExportAPI
from tests.util.mock_method import MockMethod
from tests.util.mock_telegram_update import MockTelegramUpdate


class BlacklistFunctionalityTest(unittest.TestCase):

    @patch.object(telegram, "Bot")
    def test_call__route_add_blacklisted_tag(self, bot):
        update = MockTelegramUpdate.with_message(chat_id=14358, text="/add_blacklisted_tag test")
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
        func = BlacklistFunctionality(watcher)
        add_tag = MockMethod("Added to blacklist: test")
        func._add_to_blacklist = add_tag.call

        func.call(bot, update)

        assert add_tag.called
        assert add_tag.args is not None
        assert add_tag.args[0] == 14358
        assert add_tag.args[1] == "test"
        bot.send_message.assert_called()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == "Added to blacklist: test"

    @patch.object(telegram, "Bot")
    def test_call__route_remove_blacklisted_tag(self, bot):
        update = MockTelegramUpdate.with_message(chat_id=14358, text="/remove_blacklisted_tag example")
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
        func = BlacklistFunctionality(watcher)
        remove_tag = MockMethod("Removed from blacklist: example")
        func._remove_from_blacklist = remove_tag.call

        func.call(bot, update)

        assert remove_tag.called
        assert remove_tag.args is not None
        assert remove_tag.args[0] == 14358
        assert remove_tag.args[1] == "example"
        bot.send_message.assert_called()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == "Removed from blacklist: example"

    @patch.object(telegram, "Bot")
    def test_call__route_list_blacklisted_tags(self, bot):
        update = MockTelegramUpdate.with_message(chat_id=14358, text="/list_blacklisted_tags")
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
        func = BlacklistFunctionality(watcher)
        list_tags = MockMethod("Listing blacklisted tags")
        func._list_blacklisted_tags = list_tags.call

        func.call(bot, update)

        assert list_tags.called
        assert list_tags.args is not None
        assert list_tags.args[0] == 14358
        bot.send_message.assert_called()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == "Listing blacklisted tags"

    @patch.object(telegram, "Bot")
    def test_add_to_blacklist__no_add_blank(self, bot):
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
        func = BlacklistFunctionality(watcher)

        resp = func._add_to_blacklist(18749, "")

        assert resp == "Please specify the tag you wish to add to blacklist."
        assert len(watcher.blacklists) == 0

    @patch.object(telegram, "Bot")
    def test_add_to_blacklist__creates_blacklist_for_channel(self, bot):
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
        func = BlacklistFunctionality(watcher)
        list_tags = MockMethod("Listing blacklisted tags")
        func._list_blacklisted_tags = list_tags.call

        resp = func._add_to_blacklist(18749, "test")

        assert "Added tag to blacklist" in resp
        assert "\"test\"" in resp
        assert list_tags.called
        assert list_tags.args[0] == 18749
        assert "Listing blacklisted tags" in resp
        assert len(watcher.blacklists[18749]) == 1
        assert isinstance(watcher.blacklists[18749], set)
        tag = list(watcher.blacklists[18749])[0]
        assert tag == "test"

    @patch.object(telegram, "Bot")
    def test_add_to_blacklist__add_tag_to_blacklist(self, bot):
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
        watcher.blacklists[18749] = {"example"}
        func = BlacklistFunctionality(watcher)
        list_tags = MockMethod("Listing blacklisted tags")
        func._list_blacklisted_tags = list_tags.call

        resp = func._add_to_blacklist(18749, "test")

        assert "Added tag to blacklist" in resp
        assert "\"test\"" in resp
        assert list_tags.called
        assert list_tags.args[0] == 18749
        assert "Listing blacklisted tags" in resp
        assert len(watcher.blacklists[18749]) == 2
        assert isinstance(watcher.blacklists[18749], set)
        assert "example" in watcher.blacklists[18749]
        assert "test" in watcher.blacklists[18749]

    @patch.object(telegram, "Bot")
    def test_remove_from_blacklist__tag_not_in_blacklist(self, bot):
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
        watcher.blacklists[18749] = {"example"}
        watcher.blacklists[18747] = {"test"}
        func = BlacklistFunctionality(watcher)

        resp = func._remove_from_blacklist(18749, "test")

        assert resp == "The tag \"test\" is not on the blacklist for this chat."
        assert len(watcher.blacklists) == 2
        assert len(watcher.blacklists[18749]) == 1
        assert len(watcher.blacklists[18747]) == 1

    @patch.object(telegram, "Bot")
    def test_remove_from_blacklist__removes_tag_from_blacklist(self, bot):
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
        watcher.blacklists[18749] = {"example", "test"}
        watcher.blacklists[18747] = {"test"}
        func = BlacklistFunctionality(watcher)
        list_tags = MockMethod("Listing blacklisted tags")
        func._list_blacklisted_tags = list_tags.call

        resp = func._remove_from_blacklist(18749, "test")

        assert "Removed tag from blacklist: \"test\"." in resp
        assert list_tags.called
        assert list_tags.args[0] == 18749
        assert "Listing blacklisted tags" in resp
        assert len(watcher.blacklists) == 2
        assert len(watcher.blacklists[18749]) == 1
        assert len(watcher.blacklists[18747]) == 1
        assert watcher.blacklists[18749] == {"example"}
        assert watcher.blacklists[18747] == {"test"}

    @patch.object(telegram, "Bot")
    def test_list_blacklisted_tags(self, bot):
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api, bot)
        watcher.blacklists[18749] = {"example", "deer"}
        watcher.blacklists[18747] = {"test"}
        func = BlacklistFunctionality(watcher)

        resp = func._list_blacklisted_tags(18749)

        assert "Current blacklist for this chat:" in resp
        assert "- deer" in resp
        assert "- example" in resp
        assert "- test" not in resp
