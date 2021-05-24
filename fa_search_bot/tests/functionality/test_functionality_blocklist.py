import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.subscriptions import BlocklistFunctionality
from fa_search_bot.subscription_watcher import SubscriptionWatcher
from fa_search_bot.tests.util.mock_export_api import MockExportAPI
from fa_search_bot.tests.util.mock_method import MockMethod
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent


@pytest.mark.asyncio
async def test_call__route_add_blocklisted_tag(mock_client):
    event = MockTelegramEvent.with_message(chat_id=14358, text="/add_blocklisted_tag test")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = BlocklistFunctionality(watcher)
    add_tag = MockMethod("Added to blocklist: test")
    func._add_to_blocklist = add_tag.call

    with pytest.raises(StopPropagation):
        # noinspection PyTypeChecker
        await func.call(event)

    assert add_tag.called
    assert add_tag.args is not None
    assert add_tag.args[0] == 14358
    assert add_tag.args[1] == "test"
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Added to blocklist: test"


@pytest.mark.asyncio
async def test_call__route_remove_blocklisted_tag(context):
    event = MockTelegramEvent.with_message(chat_id=14358, text="/remove_blocklisted_tag example")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = BlocklistFunctionality(watcher)
    remove_tag = MockMethod("Removed from blocklist: example")
    func._remove_from_blocklist = remove_tag.call

    with pytest.raises(StopPropagation):
        # noinspection PyTypeChecker
        await func.call(event)

    assert remove_tag.called
    assert remove_tag.args is not None
    assert remove_tag.args[0] == 14358
    assert remove_tag.args[1] == "example"
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Removed from blocklist: example"


@pytest.mark.asyncio
async def test_call__route_list_blocklisted_tags(context):
    event = MockTelegramEvent.with_message(chat_id=14358, text="/list_blocklisted_tags")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = BlocklistFunctionality(watcher)
    list_tags = MockMethod("Listing blocklisted tags")
    func._list_blocklisted_tags = list_tags.call

    with pytest.raises(StopPropagation):
        # noinspection PyTypeChecker
        await func.call(event)

    assert list_tags.called
    assert list_tags.args is not None
    assert list_tags.args[0] == 14358
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Listing blocklisted tags"


def test_add_to_blocklist__no_add_blank(context):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = BlocklistFunctionality(watcher)

    resp = func._add_to_blocklist(18749, "")

    assert resp == "Please specify the tag you wish to add to blocklist."
    assert len(watcher.blocklists) == 0


def test_add_to_blocklist__creates_blocklist_for_channel(context):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    func = BlocklistFunctionality(watcher)
    list_tags = MockMethod("Listing blocklisted tags")
    func._list_blocklisted_tags = list_tags.call

    resp = func._add_to_blocklist(18749, "test")

    assert "Added tag to blocklist" in resp
    assert "\"test\"" in resp
    assert list_tags.called
    assert list_tags.args[0] == 18749
    assert "Listing blocklisted tags" in resp
    assert len(watcher.blocklists[18749]) == 1
    assert isinstance(watcher.blocklists[18749], set)
    tag = list(watcher.blocklists[18749])[0]
    assert tag == "test"


def test_add_to_blocklist__add_tag_to_blocklist(context):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    watcher.blocklists[18749] = {"example"}
    func = BlocklistFunctionality(watcher)
    list_tags = MockMethod("Listing blocklisted tags")
    func._list_blocklisted_tags = list_tags.call

    resp = func._add_to_blocklist(18749, "test")

    assert "Added tag to blocklist" in resp
    assert "\"test\"" in resp
    assert list_tags.called
    assert list_tags.args[0] == 18749
    assert "Listing blocklisted tags" in resp
    assert len(watcher.blocklists[18749]) == 2
    assert isinstance(watcher.blocklists[18749], set)
    assert "example" in watcher.blocklists[18749]
    assert "test" in watcher.blocklists[18749]


def test_remove_from_blocklist__tag_not_in_blocklist(context):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    watcher.blocklists[18749] = {"example"}
    watcher.blocklists[18747] = {"test"}
    func = BlocklistFunctionality(watcher)

    resp = func._remove_from_blocklist(18749, "test")

    assert resp == "The tag \"test\" is not on the blocklist for this chat."
    assert len(watcher.blocklists) == 2
    assert len(watcher.blocklists[18749]) == 1
    assert len(watcher.blocklists[18747]) == 1


def test_remove_from_blocklist__removes_tag_from_blocklist(context):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    watcher.blocklists[18749] = {"example", "test"}
    watcher.blocklists[18747] = {"test"}
    func = BlocklistFunctionality(watcher)
    list_tags = MockMethod("Listing blocklisted tags")
    func._list_blocklisted_tags = list_tags.call

    resp = func._remove_from_blocklist(18749, "test")

    assert "Removed tag from blocklist: \"test\"." in resp
    assert list_tags.called
    assert list_tags.args[0] == 18749
    assert "Listing blocklisted tags" in resp
    assert len(watcher.blocklists) == 2
    assert len(watcher.blocklists[18749]) == 1
    assert len(watcher.blocklists[18747]) == 1
    assert watcher.blocklists[18749] == {"example"}
    assert watcher.blocklists[18747] == {"test"}


def test_list_blocklisted_tags(context):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, context.bot)
    watcher.blocklists[18749] = {"example", "deer"}
    watcher.blocklists[18747] = {"test"}
    func = BlocklistFunctionality(watcher)

    resp = func._list_blocklisted_tags(18749)

    assert "Current blocklist for this chat:" in resp
    assert "- deer" in resp
    assert "- example" in resp
    assert "- test" not in resp
