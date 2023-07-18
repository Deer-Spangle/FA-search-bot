from __future__ import annotations

import asyncio

import pytest

from fa_search_bot.sites.furaffinity.fa_export_api import CloudflareError
from fa_search_bot.subscriptions.subscription_watcher import SubscriptionWatcher
from fa_search_bot.tests.subscriptions.test_subscription_watcher import watcher_killer
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_submission_cache import MockSubmissionCache


@pytest.mark.skip
@pytest.mark.asyncio
async def test_get_new_results__handles_empty_latest_ids(mock_client):
    api = MockExportAPI()
    api.with_browse_results([MockSubmission("1223"), MockSubmission("1222"), MockSubmission("1220")])
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    watcher.running = True

    results = await watcher._get_new_results()

    assert len(results) == 0
    assert len(watcher.latest_ids) == 3
    assert watcher.latest_ids[0] == "1220"
    assert watcher.latest_ids[1] == "1222"
    assert watcher.latest_ids[2] == "1223"


@pytest.mark.skip
@pytest.mark.asyncio
async def test_get_new_results__returns_new_results(mock_client):
    api = MockExportAPI()
    api.with_browse_results([MockSubmission("1222"), MockSubmission("1221"), MockSubmission("1220")])
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    watcher.latest_ids.append("1220")
    watcher.running = True

    results = await watcher._get_new_results()

    assert len(results) == 2
    assert results[0].submission_id == "1221"
    assert results[1].submission_id == "1222"


@pytest.mark.skip
@pytest.mark.asyncio
async def test_get_new_results__includes_missing_ids(mock_client):
    api = MockExportAPI()
    api.with_browse_results([MockSubmission("1224"), MockSubmission("1221"), MockSubmission("1220")])
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    watcher.latest_ids.append("1220")
    watcher.running = True

    results = await watcher._get_new_results()

    assert len(results) == 4
    assert results[0].submission_id == "1221"
    assert results[1].submission_id == "1222"
    assert results[2].submission_id == "1223"
    assert results[3].submission_id == "1224"


@pytest.mark.skip
@pytest.mark.asyncio
async def test_get_new_results__requests_only_page_one(mock_client):
    api = MockExportAPI()
    api.with_browse_results([MockSubmission("1254")], page=1)
    api.call_after_x_browse = (lambda *args: (_ for _ in ()).throw(Exception), 2)
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    watcher.latest_ids.append("1250")
    watcher.running = True

    results = await watcher._get_new_results()

    assert len(results) == 4
    assert results[0].submission_id == "1251"
    assert results[1].submission_id == "1252"
    assert results[2].submission_id == "1253"
    assert results[3].submission_id == "1254"


@pytest.mark.skip
@pytest.mark.asyncio
async def test_get_new_results__handles_sub_id_drop(mock_client):
    api = MockExportAPI()
    api.with_browse_results([MockSubmission("1220")])
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    watcher.latest_ids.append("1225")
    watcher.running = True

    results = await watcher._get_new_results()

    assert len(results) == 0


@pytest.mark.skip
@pytest.mark.asyncio
async def test_get_new_results__handles_cloudflare(mock_client):
    api = MockExportAPI()

    def raise_cloudflare(*_, **__):
        raise CloudflareError()

    api.get_browse_page = raise_cloudflare
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    watcher.BROWSE_RETRY_BACKOFF = 0.1
    watcher.latest_ids.append("1225")
    watcher.running = True

    task = asyncio.get_event_loop().create_task(watcher_killer(watcher))
    results = await watcher._get_new_results()
    await task

    assert len(results) == 0
