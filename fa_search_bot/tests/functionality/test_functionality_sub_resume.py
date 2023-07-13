import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.subscriptions import SubscriptionFunctionality
from fa_search_bot.subscriptions.subscription_watcher import Subscription, SubscriptionWatcher
from fa_search_bot.tests.util.mock_export_api import MockExportAPI
from fa_search_bot.tests.util.mock_method import MockMethod
from fa_search_bot.tests.util.mock_submission_cache import MockSubmissionCache
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent


@pytest.mark.asyncio
async def test_call__route_resume_destination(mock_client):
    event = MockTelegramEvent.with_message(chat_id=14358, text="/resume")
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    func = SubscriptionFunctionality(watcher)
    resume_dest = MockMethod("Resumed all subscriptions")
    func._resume_destination = resume_dest.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert resume_dest.called
    assert resume_dest.args is not None
    assert resume_dest.args[0] == event.chat_id
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Resumed all subscriptions"


@pytest.mark.asyncio
async def test_call__route_unpause_destination(mock_client):
    event = MockTelegramEvent.with_message(chat_id=14358, text="/unpause")
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    func = SubscriptionFunctionality(watcher)
    resume_dest = MockMethod("Resumed all subscriptions")
    func._resume_destination = resume_dest.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert resume_dest.called
    assert resume_dest.args is not None
    assert resume_dest.args[0] == event.chat_id
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Resumed all subscriptions"


@pytest.mark.asyncio
async def test_call__route_resume_destination_with_handle(mock_client):
    event = MockTelegramEvent.with_message(chat_id=14358, text="/resume@FASearchBot")
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    func = SubscriptionFunctionality(watcher)
    resume_dest = MockMethod("Resumed all subscriptions")
    func._resume_destination = resume_dest.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert resume_dest.called
    assert resume_dest.args is not None
    assert resume_dest.args[0] == event.chat_id
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Resumed all subscriptions"


@pytest.mark.asyncio
async def test_call__route_resume_subscription(mock_client):
    event = MockTelegramEvent.with_message(chat_id=14358, text="/resume test")
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    func = SubscriptionFunctionality(watcher)
    resume_sub = MockMethod("Resumed subscription")
    func._resume_subscription = resume_sub.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert resume_sub.called
    assert resume_sub.args is not None
    assert resume_sub.args[0] == event.chat_id
    assert resume_sub.args[1] == "test"
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Resumed subscription"


@pytest.mark.asyncio
async def test_call__route_resume_subscription_with_handle(mock_client):
    event = MockTelegramEvent.with_message(chat_id=14358, text="/resume@FASearchBot test")
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    func = SubscriptionFunctionality(watcher)
    resume_sub = MockMethod("Resumed subscription")
    func._resume_subscription = resume_sub.call

    with pytest.raises(StopPropagation):
        await func.call(event)

    assert resume_sub.called
    assert resume_sub.args is not None
    assert resume_sub.args[0] == event.chat_id
    assert resume_sub.args[1] == "test"
    event.reply.assert_called()
    assert event.reply.call_args[0][0] == "Resumed subscription"


def test_resume_destination__no_subs(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    func = SubscriptionFunctionality(watcher)

    resp = func._resume_destination(18749)

    assert resp == "There are no subscriptions posting here to resume."
    assert len(watcher.subscriptions) == 0


def test_resume_destination__one_sub(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    sub = Subscription("test", 18749)
    sub.paused = True
    watcher.subscriptions.add(sub)
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    resp = func._resume_destination(18749)

    assert "Resumed all subscriptions" in resp
    assert list_subs.called
    assert list_subs.args[0] == 18749
    assert "Listing subscriptions" in resp
    assert len(watcher.subscriptions) == 1
    subscription = list(watcher.subscriptions)[0]
    assert subscription.query_str == "test"
    assert subscription.destination == 18749
    assert subscription.paused is False


def test_resume_destination__multiple_subs(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    sub1 = Subscription("test", 18749)
    sub1.paused = True
    watcher.subscriptions.add(sub1)
    sub2 = Subscription("example", 18749)
    sub2.paused = True
    watcher.subscriptions.add(sub2)
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    resp = func._resume_destination(18749)

    assert "Resumed all subscriptions." in resp
    assert len(watcher.subscriptions) == 2
    assert list_subs.called
    assert list_subs.args[0] == 18749
    assert "Listing subscriptions" in resp
    for subscription in watcher.subscriptions:
        assert subscription.query_str in ["test", "example"]
        assert subscription.destination == 18749
        assert subscription.paused is False


def test_resume_destination__not_in_other_destination(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    sub1 = Subscription("test", 18749)
    sub1.paused = True
    watcher.subscriptions.add(sub1)
    sub2 = Subscription("example", 12345)
    sub2.paused = True
    watcher.subscriptions.add(sub2)
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    resp = func._resume_destination(18749)

    assert "Resumed all subscriptions." in resp
    assert len(watcher.subscriptions) == 2
    assert list_subs.called
    assert list_subs.args[0] == 18749
    assert "Listing subscriptions" in resp
    sub1, sub2 = list(watcher.subscriptions)[:2]
    if sub1.destination != 18749:
        sub2, sub1 = sub1, sub2
    assert sub1.destination == 18749
    assert sub1.query_str == "test"
    assert sub1.paused is False
    assert sub2.destination == 12345
    assert sub2.query_str == "example"
    assert sub2.paused is True


def test_resume_destination__all_running(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    sub1 = Subscription("test", 18749)
    sub1.paused = False
    watcher.subscriptions.add(sub1)
    sub2 = Subscription("example", 18749)
    sub2.paused = False
    watcher.subscriptions.add(sub2)
    func = SubscriptionFunctionality(watcher)

    resp = func._resume_destination(18749)

    assert resp == "All subscriptions are already running."
    assert len(watcher.subscriptions) == 2
    for subscription in watcher.subscriptions:
        assert subscription.query_str in ["test", "example"]
        assert subscription.destination == 18749
        assert subscription.paused is False


def test_resume_destination__all_running_except_elsewhere(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    sub1 = Subscription("test", 18749)
    sub1.paused = False
    watcher.subscriptions.add(sub1)
    sub2 = Subscription("example", 12345)
    sub2.paused = True
    watcher.subscriptions.add(sub2)
    func = SubscriptionFunctionality(watcher)

    resp = func._resume_destination(18749)

    assert resp == "All subscriptions are already running."
    assert len(watcher.subscriptions) == 2
    sub1, sub2 = list(watcher.subscriptions)[:2]
    if sub1.destination != 18749:
        sub2, sub1 = sub1, sub2
    assert sub1.destination == 18749
    assert sub1.query_str == "test"
    assert sub1.paused is False
    assert sub2.destination == 12345
    assert sub2.query_str == "example"
    assert sub2.paused is True


def test_resume_subscription__no_matching(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    sub1 = Subscription("example", 18749)
    sub1.paused = True
    watcher.subscriptions.add(sub1)
    sub2 = Subscription("deer", 18749)
    sub2.paused = True
    watcher.subscriptions.add(sub2)
    func = SubscriptionFunctionality(watcher)

    resp = func._resume_subscription(18749, "test")

    assert resp == 'There is not a subscription for "test" in this chat.'
    assert len(watcher.subscriptions) == 2
    for subscription in watcher.subscriptions:
        assert subscription.paused is True


def test_resume_subscription__one_matching_in_wrong_destination(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    sub1 = Subscription("example", 18749)
    sub1.paused = True
    watcher.subscriptions.add(sub1)
    sub2 = Subscription("test", 12345)
    sub2.paused = True
    watcher.subscriptions.add(sub2)
    func = SubscriptionFunctionality(watcher)

    resp = func._resume_subscription(18749, "test")

    assert resp == 'There is not a subscription for "test" in this chat.'
    assert len(watcher.subscriptions) == 2
    for subscription in watcher.subscriptions:
        assert subscription.paused is True


def test_resume_subscription__one_matching(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    sub1 = Subscription("example", 18749)
    sub1.paused = True
    watcher.subscriptions.add(sub1)
    sub2 = Subscription("test", 18749)
    sub2.paused = True
    watcher.subscriptions.add(sub2)
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    resp = func._resume_subscription(18749, "test")

    assert 'Resumed subscription: "test".' in resp
    assert list_subs.called
    assert list_subs.args[0] == 18749
    assert "Listing subscriptions" in resp
    assert len(watcher.subscriptions) == 2
    sub1, sub2 = watcher.subscriptions
    if sub1.query_str != "test":
        sub1, sub2 = sub2, sub1
    assert sub1.query_str == "test"
    assert sub1.destination == 18749
    assert sub1.paused is False
    assert sub2.query_str == "example"
    assert sub2.destination == 18749
    assert sub2.paused is True


def test_resume_subscription__case_insensitive(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    sub1 = Subscription("EXAMPLE", 18749)
    sub1.paused = True
    watcher.subscriptions.add(sub1)
    sub2 = Subscription("TEST", 18749)
    sub2.paused = True
    watcher.subscriptions.add(sub2)
    func = SubscriptionFunctionality(watcher)
    list_subs = MockMethod("Listing subscriptions")
    func._list_subs = list_subs.call

    resp = func._resume_subscription(18749, "test")

    assert 'Resumed subscription: "test".' in resp
    assert list_subs.called
    assert list_subs.args[0] == 18749
    assert "Listing subscriptions" in resp
    assert len(watcher.subscriptions) == 2
    sub1, sub2 = watcher.subscriptions
    if sub1.query_str != "TEST":
        sub1, sub2 = sub2, sub1
    assert sub1.query_str == "TEST"
    assert sub1.destination == 18749
    assert sub1.paused is False
    assert sub2.query_str == "EXAMPLE"
    assert sub2.destination == 18749
    assert sub2.paused is True


def test_resume_subscription__already_running(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    sub1 = Subscription("example", 18749)
    sub1.paused = True
    watcher.subscriptions.add(sub1)
    sub2 = Subscription("test", 18749)
    sub2.paused = False
    watcher.subscriptions.add(sub2)
    func = SubscriptionFunctionality(watcher)

    resp = func._resume_subscription(18749, "test")

    assert resp == 'Subscription for "test" is already running.'
    assert len(watcher.subscriptions) == 2
    sub1, sub2 = watcher.subscriptions
    if sub1.query_str != "test":
        sub1, sub2 = sub2, sub1
    assert sub1.query_str == "test"
    assert sub1.destination == 18749
    assert sub1.paused is False
    assert sub2.query_str == "example"
    assert sub2.destination == 18749
    assert sub2.paused is True
