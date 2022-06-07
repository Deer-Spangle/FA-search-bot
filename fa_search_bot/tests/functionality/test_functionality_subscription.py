import datetime

import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.subscriptions import SubscriptionFunctionality
from fa_search_bot.subscription_watcher import Subscription, SubscriptionWatcher
from fa_search_bot.tests.util.mock_export_api import MockExportAPI
from fa_search_bot.tests.util.mock_method import MockMethod
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent


@pytest.mark.asyncio
async def test_call__route_add_subscription(mock_client):
    event = MockTelegramEvent.with_message(chat_id=14358, text="/add_subscription test")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SubscriptionFunctionality(watcher)
    add_sub = MockMethod("Added subscription test")
    func._add_sub = add_sub.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert add_sub.called
    assert add_sub.args is not None
    assert add_sub.args[0] == 14358
    assert add_sub.args[1] == "test"
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Added subscription test"


@pytest.mark.asyncio
async def test_call__route_add_subscription_with_username(mock_client):
    event = MockTelegramEvent.with_message(
        chat_id=14358, text="/add_subscription@FASearchBot test"
    )
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SubscriptionFunctionality(watcher)
    add_sub = MockMethod("Added subscription test")
    func._add_sub = add_sub.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert add_sub.called
    assert add_sub.args is not None
    assert add_sub.args[0] == 14358
    assert add_sub.args[1] == "test"
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Added subscription test"


@pytest.mark.asyncio
async def test_call__route_remove_subscription(mock_client):
    event = MockTelegramEvent.with_message(
        chat_id=14358, text="/remove_subscription example"
    )
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SubscriptionFunctionality(watcher)
    delete_sub = MockMethod("Removed subscription test")
    func._remove_sub = delete_sub.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert delete_sub.called
    assert delete_sub.args is not None
    assert delete_sub.args[0] == 14358
    assert delete_sub.args[1] == "example"
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Removed subscription test"


@pytest.mark.asyncio
async def test_call__route_remove_subscription_with_username(mock_client):
    event = MockTelegramEvent.with_message(
        chat_id=14358, text="/remove_subscription@FASearchBot example"
    )
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SubscriptionFunctionality(watcher)
    delete_sub = MockMethod("Removed subscription test")
    func._remove_sub = delete_sub.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert delete_sub.called
    assert delete_sub.args is not None
    assert delete_sub.args[0] == 14358
    assert delete_sub.args[1] == "example"
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Removed subscription test"


@pytest.mark.asyncio
async def test_call__route_list_subscriptions(mock_client):
    event = MockTelegramEvent.with_message(chat_id=14358, text="/list_subscriptions")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert list_subs.called
    assert list_subs.args is not None
    assert list_subs.args[0] == 14358
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Listing subscriptions"


@pytest.mark.asyncio
async def test_call__route_list_subscriptions_with_username(mock_client):
    event = MockTelegramEvent.with_message(
        chat_id=14358, text="/list_subscriptions@FASearchBot"
    )
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert list_subs.called
    assert list_subs.args is not None
    assert list_subs.args[0] == 14358
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Listing subscriptions"


def test_add_sub__no_add_blank(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SubscriptionFunctionality(watcher)

    resp = func._add_sub(18749, "")

    assert resp == "Please specify the subscription query you wish to add."
    assert len(watcher.subscriptions) == 0


def test_add_sub__invalid_query(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SubscriptionFunctionality(watcher)

    resp = func._add_sub(18749, "(hello")

    assert resp.startswith("Failed to parse subscription query")
    assert len(watcher.subscriptions) == 0


def test_add_sub__no_add_duplicate(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("test", 18749))
    func = SubscriptionFunctionality(watcher)

    resp = func._add_sub(18749, "test")

    assert resp == 'A subscription already exists for "test".'
    assert len(watcher.subscriptions) == 1


def test_add_sub__no_add_duplicate_case_insensitive(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("test", 18749))
    func = SubscriptionFunctionality(watcher)

    resp = func._add_sub(18749, "TEST")

    assert resp == 'A subscription already exists for "TEST".'
    assert len(watcher.subscriptions) == 1


def test_add_sub__adds_subscription(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    resp = func._add_sub(18749, "test")

    assert "Added subscription" in resp
    assert '"test"' in resp
    assert list_subs.called
    assert list_subs.args[0] == 18749
    assert "Listing subscriptions" in resp
    assert len(watcher.subscriptions) == 1
    subscription = list(watcher.subscriptions)[0]
    assert subscription.query_str == "test"
    assert subscription.destination == 18749
    assert subscription.latest_update is None


def test_remove_sub__non_existent_subscription(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("example", 18749))
    watcher.subscriptions.add(Subscription("test", 18747))
    func = SubscriptionFunctionality(watcher)

    resp = func._remove_sub(18749, "test")

    assert resp == 'There is not a subscription for "test" in this chat.'
    assert len(watcher.subscriptions) == 2


def test_remove_sub__removes_subscription(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("example", 18749))
    watcher.subscriptions.add(Subscription("test", 18747))
    new_sub = Subscription("test", 18749)
    new_sub.latest_update = datetime.datetime.now()
    watcher.subscriptions.add(new_sub)
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    resp = func._remove_sub(18749, "test")

    assert 'Removed subscription: "test".' in resp
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


def test_remove_sub__removes_subscription_case_insensitive(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("example", 18749))
    watcher.subscriptions.add(Subscription("test", 18747))
    new_sub = Subscription("test", 18749)
    new_sub.latest_update = datetime.datetime.now()
    watcher.subscriptions.add(new_sub)
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    resp = func._remove_sub(18749, "TEST")

    assert 'Removed subscription: "TEST".' in resp
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


def test_list_subs(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("example", 18749))
    watcher.subscriptions.add(Subscription("test", 18747))
    watcher.subscriptions.add(Subscription("deer", 18749))
    func = SubscriptionFunctionality(watcher)

    resp = func._list_subs(18749)

    assert "Current subscriptions in this chat:" in resp
    assert "- deer" in resp
    assert "- example" in resp
    assert "- test" not in resp


def test_list_subs__alphabetical(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("example", 18749))
    watcher.subscriptions.add(Subscription("test", 18749))
    watcher.subscriptions.add(Subscription("deer", 18749))
    func = SubscriptionFunctionality(watcher)

    resp = func._list_subs(18749)

    assert "Current subscriptions in this chat:" in resp
    assert "- deer\n- example\n- test" in resp


def test_list_subs__alphabetical_case_insensitive(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("Example", 18749))
    watcher.subscriptions.add(Subscription("test", 18749))
    watcher.subscriptions.add(Subscription("deer", 18749))
    func = SubscriptionFunctionality(watcher)

    resp = func._list_subs(18749)

    assert "Current subscriptions in this chat:" in resp
    assert "- deer\n- Example\n- test" in resp


def test_list_subs__some_paused(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("example", 18749))
    sub_paused = Subscription("test", 18749)
    sub_paused.paused = True
    watcher.subscriptions.add(sub_paused)
    watcher.subscriptions.add(Subscription("deer", 18749))
    func = SubscriptionFunctionality(watcher)

    resp = func._list_subs(18749)

    assert "Current subscriptions in this chat:" in resp
    assert "- deer\n- example\n- ⏸<s>test</s>" in resp
