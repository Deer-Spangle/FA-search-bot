import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.subscriptions import SubscriptionFunctionality
from fa_search_bot.subscription_watcher import Subscription, SubscriptionWatcher
from fa_search_bot.tests.util.mock_export_api import MockExportAPI
from fa_search_bot.tests.util.mock_method import MockMethod
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent


@pytest.mark.asyncio
async def test_call__route_pause_destination(mock_client):
    event = MockTelegramEvent.with_message(chat_id=14358, text="/pause")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SubscriptionFunctionality(watcher)
    pause_dest = MockMethod("Paused all subscriptions")
    func._pause_destination = pause_dest.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert pause_dest.called
    assert pause_dest.args is not None
    assert pause_dest.args[0] == event.chat_id
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Paused all subscriptions"


@pytest.mark.asyncio
async def test_call__route_suspend_destination(mock_client):
    event = MockTelegramEvent.with_message(chat_id=14358, text="/suspend")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SubscriptionFunctionality(watcher)
    pause_dest = MockMethod("Paused all subscriptions")
    func._pause_destination = pause_dest.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert pause_dest.called
    assert pause_dest.args is not None
    assert pause_dest.args[0] == event.chat_id
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Paused all subscriptions"


@pytest.mark.asyncio
async def test_call__route_pause_destination_with_handle(mock_client):
    event = MockTelegramEvent.with_message(chat_id=14358, text="/pause@FASearchBot")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SubscriptionFunctionality(watcher)
    pause_dest = MockMethod("Paused all subscriptions")
    func._pause_destination = pause_dest.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert pause_dest.called
    assert pause_dest.args is not None
    assert pause_dest.args[0] == event.chat_id
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Paused all subscriptions"


@pytest.mark.asyncio
async def test_call__route_pause_subscription(mock_client):
    event = MockTelegramEvent.with_message(chat_id=14358, text="/pause test")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SubscriptionFunctionality(watcher)
    pause_sub = MockMethod("Paused subscription")
    func._pause_subscription = pause_sub.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert pause_sub.called
    assert pause_sub.args is not None
    assert pause_sub.args[0] == event.chat_id
    assert pause_sub.args[1] == "test"
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Paused subscription"


@pytest.mark.asyncio
async def test_call__route_pause_subscription_with_handle(mock_client):
    event = MockTelegramEvent.with_message(chat_id=14358, text="/pause@FASearchBot test")
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SubscriptionFunctionality(watcher)
    pause_sub = MockMethod("Paused subscription")
    func._pause_subscription = pause_sub.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert pause_sub.called
    assert pause_sub.args is not None
    assert pause_sub.args[0] == event.chat_id
    assert pause_sub.args[1] == "test"
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Paused subscription"


def test_pause_destination__no_subs(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    func = SubscriptionFunctionality(watcher)

    resp = func._pause_destination(18749)

    assert resp == "There are no subscriptions posting here to pause."
    assert len(watcher.subscriptions) == 0


def test_pause_destination__one_sub(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("test", 18749))
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    resp = func._pause_destination(18749)

    assert "Paused all subscriptions." in resp
    assert list_subs.called
    assert list_subs.args[0] == 18749
    assert "Listing subscriptions" in resp
    assert len(watcher.subscriptions) == 1
    subscription = list(watcher.subscriptions)[0]
    assert subscription.query_str == "test"
    assert subscription.destination == 18749
    assert subscription.paused is True


def test_pause_destination__multiple_subs(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("test", 18749))
    watcher.subscriptions.add(Subscription("example", 18749))
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    resp = func._pause_destination(18749)

    assert "Paused all subscriptions." in resp
    assert len(watcher.subscriptions) == 2
    assert list_subs.called
    assert list_subs.args[0] == 18749
    assert "Listing subscriptions" in resp
    for subscription in watcher.subscriptions:
        assert subscription.query_str in ["test", "example"]
        assert subscription.destination == 18749
        assert subscription.paused is True


def test_pause_destination__not_in_other_destination(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("test", 18749))
    watcher.subscriptions.add(Subscription("example", 12345))
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    resp = func._pause_destination(18749)

    assert "Paused all subscriptions." in resp
    assert len(watcher.subscriptions) == 2
    assert list_subs.called
    assert list_subs.args[0] == 18749
    assert "Listing subscriptions" in resp
    sub1, sub2 = list(watcher.subscriptions)[:2]
    if sub1.destination != 18749:
        sub2, sub1 = sub1, sub2
    assert sub1.destination == 18749
    assert sub1.query_str == "test"
    assert sub1.paused is True
    assert sub2.destination == 12345
    assert sub2.query_str == "example"
    assert sub2.paused is False


def test_pause_destination__all_paused(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    sub1 = Subscription("test", 18749)
    sub1.paused = True
    watcher.subscriptions.add(sub1)
    sub2 = Subscription("example", 18749)
    sub2.paused = True
    watcher.subscriptions.add(sub2)
    func = SubscriptionFunctionality(watcher)

    resp = func._pause_destination(18749)

    assert resp == "All subscriptions are already paused."
    assert len(watcher.subscriptions) == 2
    for subscription in watcher.subscriptions:
        assert subscription.query_str in ["test", "example"]
        assert subscription.destination == 18749
        assert subscription.paused is True


def test_pause_destination__all_paused_except_elsewhere(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    sub1 = Subscription("test", 18749)
    sub1.paused = True
    watcher.subscriptions.add(sub1)
    sub2 = Subscription("example", 12345)
    sub2.paused = False
    watcher.subscriptions.add(sub2)
    func = SubscriptionFunctionality(watcher)

    resp = func._pause_destination(18749)

    assert resp == "All subscriptions are already paused."
    assert len(watcher.subscriptions) == 2
    sub1, sub2 = list(watcher.subscriptions)[:2]
    if sub1.destination != 18749:
        sub2, sub1 = sub1, sub2
    assert sub1.destination == 18749
    assert sub1.query_str == "test"
    assert sub1.paused is True
    assert sub2.destination == 12345
    assert sub2.query_str == "example"
    assert sub2.paused is False


def test_pause_subscription__no_matching(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("example", 18749))
    watcher.subscriptions.add(Subscription("deer", 18749))
    func = SubscriptionFunctionality(watcher)

    resp = func._pause_subscription(18749, "test")

    assert resp == 'There is not a subscription for "test" in this chat.'
    assert len(watcher.subscriptions) == 2
    for subscription in watcher.subscriptions:
        assert subscription.paused is False


def test_pause_subscription__one_matching_in_wrong_destination(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("example", 18749))
    watcher.subscriptions.add(Subscription("test", 12345))
    func = SubscriptionFunctionality(watcher)

    resp = func._pause_subscription(18749, "test")

    assert resp == 'There is not a subscription for "test" in this chat.'
    assert len(watcher.subscriptions) == 2
    for subscription in watcher.subscriptions:
        assert subscription.paused is False


def test_pause_subscription__one_matching(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("example", 18749))
    watcher.subscriptions.add(Subscription("test", 18749))
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    resp = func._pause_subscription(18749, "test")

    assert 'Paused subscription: "test".' in resp
    assert list_subs.called
    assert list_subs.args[0] == 18749
    assert "Listing subscriptions" in resp
    assert len(watcher.subscriptions) == 2
    sub1, sub2 = watcher.subscriptions
    if sub1.query_str != "test":
        sub1, sub2 = sub2, sub1
    assert sub1.query_str == "test"
    assert sub1.destination == 18749
    assert sub1.paused is True
    assert sub2.query_str == "example"
    assert sub2.destination == 18749
    assert sub2.paused is False


def test_pause_subscription__case_insensitive(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("EXAMPLE", 18749))
    watcher.subscriptions.add(Subscription("TEST", 18749))
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    resp = func._pause_subscription(18749, "test")

    assert 'Paused subscription: "test".' in resp
    assert list_subs.called
    assert list_subs.args[0] == 18749
    assert "Listing subscriptions" in resp
    assert len(watcher.subscriptions) == 2
    sub1, sub2 = watcher.subscriptions
    if sub1.query_str != "TEST":
        sub1, sub2 = sub2, sub1
    assert sub1.query_str == "TEST"
    assert sub1.destination == 18749
    assert sub1.paused is True
    assert sub2.query_str == "EXAMPLE"
    assert sub2.destination == 18749
    assert sub2.paused is False


def test_pause_subscription__already_paused(mock_client):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, mock_client)
    watcher.subscriptions.add(Subscription("example", 18749))
    sub = Subscription("test", 18749)
    sub.paused = True
    watcher.subscriptions.add(sub)
    func = SubscriptionFunctionality(watcher)

    resp = func._pause_subscription(18749, "test")

    assert resp == 'Subscription for "test" is already paused.'
    assert len(watcher.subscriptions) == 2
    sub1, sub2 = watcher.subscriptions
    if sub1.query_str != "test":
        sub1, sub2 = sub2, sub1
    assert sub1.query_str == "test"
    assert sub1.destination == 18749
    assert sub1.paused is True
    assert sub2.query_str == "example"
    assert sub2.destination == 18749
    assert sub2.paused is False
