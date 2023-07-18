from __future__ import annotations

from unittest import mock

import pytest
from telethon.errors import UserIsBlockedError, InputUserDeactivatedError

from fa_search_bot.subscriptions.subscription import Subscription
from fa_search_bot.subscriptions.subscription_watcher import SubscriptionWatcher
from fa_search_bot.tests.util.mock_export_api import MockExportAPI
from fa_search_bot.tests.util.mock_submission_cache import MockSubmissionCache
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder


@pytest.mark.skip
@pytest.mark.asyncio
async def test_send_updates__sends_message(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    subscription = Subscription("test", 12345)
    submission = SubmissionBuilder().build_mock_submission()

    with mock.patch("fa_search_bot.sites.furaffinity.fa_handler.SendableFASubmission.send_message") as m:
        await watcher._send_updates([subscription], submission)

    assert m.asset_called_once()
    args, kwargs = m.call_args
    assert args[0] == mock_client
    assert args[1] == 12345
    assert "update" in kwargs["prefix"].lower()
    assert '"test"' in kwargs["prefix"]
    assert "subscription" in kwargs["prefix"].lower()


@pytest.mark.skip
@pytest.mark.asyncio
async def test_send_updates__gathers_subscriptions(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    subscription1 = Subscription("test", 12345)
    subscription2 = Subscription("test2", 12345)
    subscription3 = Subscription("test", 54321)
    submission = SubmissionBuilder().build_mock_submission()

    with mock.patch("fa_search_bot.sites.furaffinity.fa_handler.SendableFASubmission.send_message") as m:
        await watcher._send_updates([subscription1, subscription2, subscription3], submission)

    assert m.call_count == 2
    call_list = m.call_args_list
    # Indifferent to call order, so figure out the order here
    call1 = call_list[0]
    call2 = call_list[1]
    if call1[0][1] != 12345:
        call1 = call_list[1]
        call2 = call_list[0]
    args1, kwargs1 = call1
    args2, kwargs2 = call2
    # Check call matching two subscriptions
    assert args1[0] == mock_client
    assert args2[0] == mock_client
    assert args1[1] == 12345
    assert args2[1] == 54321
    assert "update" in kwargs1["prefix"].lower()
    assert '"test", "test2"' in kwargs1["prefix"]
    assert "subscriptions:" in kwargs1["prefix"].lower()
    # And check the one subscription call
    assert "update" in kwargs2["prefix"].lower()
    assert '"test"' in kwargs2["prefix"]
    assert "subscription:" in kwargs2["prefix"].lower()


@pytest.mark.skip
@pytest.mark.asyncio
async def test_send_updates__updates_latest(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    subscription = Subscription("test", 12345)
    submission = SubmissionBuilder().build_mock_submission()

    await watcher._send_updates([subscription], submission)

    assert subscription.latest_update is not None


@pytest.mark.skip
@pytest.mark.asyncio
async def test_send_updates__blocked_pauses_subs(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    subscription = Subscription("test", 12345)
    watcher.subscriptions.add(subscription)
    submission = SubmissionBuilder().build_mock_submission()

    def throw_blocked(*args, **kwargs):
        raise UserIsBlockedError(None)

    with mock.patch(
        "fa_search_bot.sites.furaffinity.fa_handler.SendableFASubmission.send_message",
        throw_blocked,
    ):
        await watcher._send_updates([subscription], submission)

    assert subscription.paused


@pytest.mark.skip
@pytest.mark.asyncio
async def test_send_updates__deleted_pauses_subs(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    subscription = Subscription("test", 12345)
    watcher.subscriptions.add(subscription)
    submission = SubmissionBuilder().build_mock_submission()

    def throw_deleted(*args, **kwargs):
        raise InputUserDeactivatedError(None)

    with mock.patch(
        "fa_search_bot.sites.furaffinity.fa_handler.SendableFASubmission.send_message",
        throw_deleted,
    ):
        await watcher._send_updates([subscription], submission)

    assert subscription.paused


@pytest.mark.skip
@pytest.mark.asyncio
async def test_send_updates__blocked_pauses_other_subs(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    subscription1 = Subscription("test", 12345)
    subscription2 = Subscription("other", 12345)
    subscription3 = Subscription("not me", 54321)
    watcher.subscriptions = {subscription1, subscription2, subscription3}
    submission = SubmissionBuilder().build_mock_submission()

    def throw_blocked(*_, **__):
        raise UserIsBlockedError(None)

    with mock.patch(
        "fa_search_bot.sites.furaffinity.fa_handler.SendableFASubmission.send_message",
        throw_blocked,
    ):
        await watcher._send_updates([subscription1], submission)

    assert subscription1.paused
    assert subscription2.paused
    assert not subscription3.paused
