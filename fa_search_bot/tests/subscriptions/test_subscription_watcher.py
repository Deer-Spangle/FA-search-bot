from __future__ import annotations

import asyncio
import datetime
import json
import os
from typing import TYPE_CHECKING

import pytest

from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.subscriptions.query_parser import AndQuery, NotQuery, WordQuery
from fa_search_bot.subscriptions.subscription_watcher import SubscriptionWatcher
from fa_search_bot.subscriptions.subscription import Subscription
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_method import MockMethod
from fa_search_bot.tests.util.mock_submission_cache import MockSubmissionCache
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder

if TYPE_CHECKING:
    from typing import List

    from fa_search_bot.sites.furaffinity.fa_submission import FASubmissionFull


class MockSubscription(Subscription):
    def __init__(self, query, destination):
        super().__init__(query, destination)
        self.submissions_checked = []
        self.blocklists = []

    def matches_result(self, result: FASubmissionFull, blocklist: List[str]) -> bool:
        self.submissions_checked.append(result)
        self.blocklists.append(blocklist)
        return True

    def send(self, result: FASubmissionFull):
        pass


# noinspection DuplicatedCode
async def watcher_killer(watcher: SubscriptionWatcher):
    # Wait until watcher is running
    while watcher.running is False:
        await asyncio.sleep(0.1)
    # Stop watcher
    watcher.running = False


def test_init(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    s = SubscriptionWatcher(api, mock_client, cache)

    assert s.api == api
    assert len(s.latest_ids) == 0
    assert len(s.subscriptions) == 0


@pytest.mark.skip
@pytest.mark.asyncio
async def test_run__is_stopped_by_running_false(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    s = SubscriptionWatcher(api, mock_client, cache)
    # Shorten the wait
    s.BACK_OFF = 1

    task = asyncio.get_event_loop().create_task(watcher_killer(s))

    # Run watcher
    await s.run()

    assert True
    await task


@pytest.mark.skip
@pytest.mark.asyncio
async def test_run__calls_get_new_results(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    method_called = MockMethod([])
    watcher._get_new_results = method_called.async_call
    # Shorten the wait
    watcher.BACK_OFF = 1

    task = asyncio.get_event_loop().create_task(watcher_killer(watcher))
    # Run watcher
    await watcher.run()
    await task

    assert method_called.called


@pytest.mark.skip
@pytest.mark.asyncio
async def test_run__calls_update_latest_ids(mock_client):
    submission1 = MockSubmission("12322")
    submission2 = MockSubmission("12324")
    api = MockExportAPI().with_submissions([submission1, submission2])
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    mock_new_results = MockMethod([submission1, submission2])
    watcher._get_new_results = mock_new_results.async_call
    mock_update_latest = MockMethod()
    watcher._update_latest_ids = mock_update_latest.call
    # Shorten the wait
    watcher.BACK_OFF = 1

    task = asyncio.get_event_loop().create_task(watcher_killer(watcher))
    # Run watcher
    await watcher.run()
    await task

    assert mock_update_latest.called
    assert mock_update_latest.args[0] == [submission2]


@pytest.mark.skip
@pytest.mark.asyncio
async def test_run__updates_latest_ids(mock_client):
    submission1 = MockSubmission("12322")
    submission2 = MockSubmission("12324")
    api = MockExportAPI().with_submissions([submission1, submission2])
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    mock_new_results = MockMethod([submission1, submission2])
    watcher._get_new_results = mock_new_results.async_call
    mock_save_json = MockMethod()
    watcher.save_to_json = mock_save_json.call
    # Shorten the wait
    watcher.BACK_OFF = 1

    task = asyncio.get_event_loop().create_task(watcher_killer(watcher))
    # Run watcher
    await watcher.run()
    await task

    assert mock_save_json.called
    assert submission1.submission_id in watcher.latest_ids
    assert submission2.submission_id in watcher.latest_ids


@pytest.mark.skip
@pytest.mark.asyncio
async def test_run__checks_all_subscriptions(mock_client):
    submission = MockSubmission("12322")
    api = MockExportAPI().with_submission(submission)
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    method_called = MockMethod([submission])
    watcher._get_new_results = method_called.async_call
    watcher.BACK_OFF = 1
    sub1 = MockSubscription("deer", 0)
    sub2 = MockSubscription("dog", 0)
    watcher.subscriptions = [sub1, sub2]

    task = asyncio.get_event_loop().create_task(watcher_killer(watcher))
    # Run watcher
    await watcher.run()
    await task

    assert submission in sub1.submissions_checked
    assert submission in sub2.submissions_checked
    assert method_called.called


@pytest.mark.skip
@pytest.mark.asyncio
async def test_run__checks_all_new_results(mock_client):
    submission1 = MockSubmission("12322")
    submission2 = MockSubmission("12324")
    api = MockExportAPI().with_submissions([submission1, submission2])
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    method_called = MockMethod([submission1, submission2])
    watcher._get_new_results = method_called.async_call
    watcher.BACK_OFF = 1
    sub = MockSubscription("deer", 0)
    watcher.subscriptions = [sub]

    task = asyncio.get_event_loop().create_task(watcher_killer(watcher))
    # Run watcher
    await watcher.run()
    await task

    assert submission1 in sub.submissions_checked
    assert submission2 in sub.submissions_checked
    assert method_called.called


@pytest.mark.skip
@pytest.mark.asyncio
async def test_run__sleeps_backoff_time(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    # Shorten the wait
    watcher.BACK_OFF = 3

    api.call_after_x_browse = (lambda: watcher.stop(), 2)

    # Run watcher
    start_time = datetime.datetime.now()
    await watcher.run()
    end_time = datetime.datetime.now()

    time_waited = end_time - start_time
    assert 3 <= time_waited.seconds <= 5


@pytest.mark.skip
@pytest.mark.asyncio
async def test_run__can_exit_fast(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    # Shorten the wait
    watcher.BACK_OFF = 3

    task = asyncio.get_event_loop().create_task(watcher_killer(watcher))

    # Run watcher
    start_time = datetime.datetime.now()
    await watcher.run()
    end_time = datetime.datetime.now()
    await task

    time_waited = end_time - start_time
    assert time_waited.seconds <= 1


@pytest.mark.skip
@pytest.mark.asyncio
async def test_run__failed_to_send_doesnt_kill_watcher(mock_client):
    submission = MockSubmission("12322")
    api = MockExportAPI().with_browse_results([submission], 1)
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    submission.send_message = lambda *args: (_ for _ in ()).throw(Exception)
    watcher.BACK_OFF = 3
    sub1 = MockSubscription("deer", 0)
    watcher.subscriptions = [sub1]

    api.call_after_x_browse = (lambda: watcher.stop(), 2)
    # Run watcher
    start_time = datetime.datetime.now()
    await watcher.run()
    end_time = datetime.datetime.now()

    time_waited = end_time - start_time
    assert 3 <= time_waited.seconds <= 5


@pytest.mark.skip
@pytest.mark.asyncio
async def test_run__passes_correct_blocklists_to_subscriptions(mock_client):
    submission = MockSubmission("12322")
    api = MockExportAPI().with_submission(submission)
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    method_called = MockMethod([submission])
    watcher._get_new_results = method_called.async_call
    watcher.BACK_OFF = 1
    watcher.blocklists = {156: {"test", "ych"}, -200: {"example"}}
    sub1 = MockSubscription("deer", 156)
    sub2 = MockSubscription("dog", -232)
    watcher.subscriptions = [sub1, sub2]

    task = asyncio.get_event_loop().create_task(watcher_killer(watcher))
    # Run watcher
    await watcher.run()
    await task

    assert submission in sub1.submissions_checked
    assert len(sub1.blocklists) == 1
    assert sub1.blocklists[0] in [
        AndQuery([NotQuery(WordQuery("test")), NotQuery(WordQuery("ych"))]),
        AndQuery([NotQuery(WordQuery("ych")), NotQuery(WordQuery("test"))]),
    ]
    assert submission in sub2.submissions_checked
    assert len(sub2.blocklists) == 1
    assert sub2.blocklists[0] == AndQuery([])
    assert method_called.called


def test_update_latest_ids(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    sub_id_str = "12345"
    sub_id = SubmissionID("xx", sub_id_str)
    mock_save_json = MockMethod()
    watcher.save_to_json = mock_save_json.call

    watcher.update_latest_id(sub_id)

    assert sub_id_str in list(watcher.latest_ids)
    assert mock_save_json.called


def test_add_to_blocklist__new_blocklist(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)

    watcher.add_to_blocklist(18749, "test")

    assert len(watcher.blocklists[18749]) == 1
    assert isinstance(watcher.blocklists[18749], set)
    assert watcher.blocklists[18749] == {"test"}


def test_add_to_blocklist__append_blocklist(mock_client):
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    watcher.blocklists[18749] = {"example"}

    watcher.add_to_blocklist(18749, "test")

    assert len(watcher.blocklists[18749]) == 2
    assert isinstance(watcher.blocklists[18749], set)
    assert watcher.blocklists[18749] == {"test", "example"}


def test_migrate_no_block_queries(mock_client):
    old_chat_id = 12345
    new_chat_id = 54321
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    watcher.subscriptions.add(MockSubscription("ych", old_chat_id))

    watcher.migrate_chat(old_chat_id, new_chat_id)

    assert len(watcher.subscriptions) == 1
    sub = list(watcher.subscriptions)[0]
    assert sub.query_str == "ych"
    assert sub.destination == new_chat_id


def test_migrate_with_block_queries(mock_client):
    old_chat_id = 12345
    new_chat_id = 54321
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    watcher.subscriptions.add(MockSubscription("ych", old_chat_id))
    watcher.add_to_blocklist(old_chat_id, "test")

    watcher.migrate_chat(old_chat_id, new_chat_id)

    assert len(watcher.blocklists[new_chat_id]) == 1
    assert old_chat_id not in watcher.blocklists
    assert isinstance(watcher.blocklists[new_chat_id], set)
    assert watcher.blocklists[new_chat_id] == {"test"}
    assert len(watcher.subscriptions) == 1
    sub = list(watcher.subscriptions)[0]
    assert sub.query_str == "ych"
    assert sub.destination == new_chat_id


def test_migrate_nothing_matching(mock_client):
    old_chat_id = 12345
    new_chat_id = 54321
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    watcher.subscriptions.add(MockSubscription("ych", new_chat_id))
    watcher.add_to_blocklist(new_chat_id, "test")

    watcher.migrate_chat(old_chat_id, new_chat_id)

    assert len(watcher.blocklists[new_chat_id]) == 1
    assert old_chat_id not in watcher.blocklists
    assert isinstance(watcher.blocklists[new_chat_id], set)
    assert watcher.blocklists[new_chat_id] == {"test"}
    assert len(watcher.subscriptions) == 1
    sub = list(watcher.subscriptions)[0]
    assert sub.query_str == "ych"
    assert sub.destination == new_chat_id


def test_migrate_merge_blocklists(mock_client):
    old_chat_id = 12345
    new_chat_id = 54321
    api = MockExportAPI()
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    watcher.subscriptions.add(MockSubscription("deer", old_chat_id))
    watcher.add_to_blocklist(old_chat_id, "test")
    watcher.subscriptions.add(MockSubscription("ych", new_chat_id))
    watcher.add_to_blocklist(new_chat_id, "example")

    watcher.migrate_chat(old_chat_id, new_chat_id)

    assert len(watcher.blocklists[new_chat_id]) == 2
    assert old_chat_id not in watcher.blocklists
    assert isinstance(watcher.blocklists[new_chat_id], set)
    assert watcher.blocklists[new_chat_id] == {"test", "example"}
    assert len(watcher.subscriptions) == 2
    for sub in watcher.subscriptions:
        assert sub.destination == new_chat_id
        assert sub.query_str in ["deer", "ych"]


def test_save_to_json(mock_client):
    test_watcher_file = "./test_subscription_watcher.json"
    if os.path.exists(test_watcher_file):
        os.remove(test_watcher_file)
    api = MockExportAPI()
    latest_submissions = [
        SubmissionBuilder(submission_id="123243").build_short_submission(),
        SubmissionBuilder(submission_id="123242").build_short_submission(),
        SubmissionBuilder(submission_id="123240").build_short_submission(),
    ]
    subscription1 = Subscription("query", 1234)
    subscription2 = Subscription("example", 5678)
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    for submission in latest_submissions[::-1]:
        watcher.update_latest_id(SubmissionID("fa", submission.submission_id))
    watcher.subscriptions.add(subscription1)
    watcher.subscriptions.add(subscription2)
    watcher.blocklists[3452] = {"test", "example"}
    watcher.blocklists[1453] = {"ych"}
    watcher.FILENAME = test_watcher_file

    try:
        watcher.save_to_json()

        assert os.path.exists(test_watcher_file)
        with open(test_watcher_file, "r") as f:
            data = json.load(f)
        assert data is not None
        assert len(data["latest_ids"]) == 3
        assert "123240" in data["latest_ids"]
        assert "123242" in data["latest_ids"]
        assert "123243" in data["latest_ids"]
        assert len(data["destinations"]) == 4
        assert len(data["destinations"]["1234"]["subscriptions"]) == 1
        assert data["destinations"]["1234"]["subscriptions"][0]["query"] == "query"
        assert len(data["destinations"]["1234"]["blocks"]) == 0

        assert len(data["destinations"]["5678"]["subscriptions"]) == 1
        assert data["destinations"]["5678"]["subscriptions"][0]["query"] == "example"
        assert len(data["destinations"]["5678"]["blocks"]) == 0

        assert len(data["destinations"]["3452"]["subscriptions"]) == 0
        assert len(data["destinations"]["3452"]["blocks"]) == 2
        assert set([block["query"] for block in data["destinations"]["3452"]["blocks"]]) == {"test", "example"}

        assert len(data["destinations"]["1453"]["subscriptions"]) == 0
        assert len(data["destinations"]["1453"]["blocks"]) == 1
        assert data["destinations"]["1453"]["blocks"][0]["query"] == "ych"
    finally:
        os.remove(test_watcher_file)


def test_from_json(mock_client):
    test_watcher_file = "./test_subscription_watcher.json"
    if os.path.exists(test_watcher_file):
        os.remove(test_watcher_file)
    old_filename = SubscriptionWatcher.FILENAME
    SubscriptionWatcher.FILENAME = test_watcher_file
    try:
        data = {
            "latest_ids": ["12423", "12422", "12420"],
            "destinations": {
                "87238": {
                    "subscriptions": [
                        {
                            "query": "test",
                            "latest_update": "2019-10-26T18:57:09",
                            "paused": False,
                        },
                    ],
                    "blocks": [],
                },
                "-87023": {
                    "subscriptions": [
                        {
                            "query": "example",
                            "latest_update": "2019-10-25T17:34:08",
                            "paused": False,
                        },
                    ],
                    "blocks": [],
                },
                "8732": {
                    "subscriptions": [],
                    "blocks": [
                        {
                            "query": "example"
                        },
                        {
                            "query": "ych",
                        },
                    ],
                },
                "-123": {
                    "subscriptions": [],
                    "blocks": [
                        {
                            "query": "fred",
                        },
                    ],
                },
            },
        }
        with open(test_watcher_file, "w+") as f:
            json.dump(data, f)
        api = MockExportAPI()
        cache = MockSubmissionCache()

        watcher = SubscriptionWatcher.load_from_json(api, mock_client, cache)

        assert len(watcher.latest_ids) == 3
        assert "12423" in watcher.latest_ids
        assert "12422" in watcher.latest_ids
        assert "12420" in watcher.latest_ids
        assert len(watcher.subscriptions) == 2
        list_subs = list(watcher.subscriptions)
        if list_subs[0].query_str == "test":
            assert list_subs[0].destination == 87238
            assert list_subs[0].latest_update == datetime.datetime(2019, 10, 26, 18, 57, 9)
            assert list_subs[1].query_str == "example"
            assert list_subs[1].destination == -87023
            assert list_subs[1].latest_update == datetime.datetime(2019, 10, 25, 17, 34, 8)
        else:
            assert list_subs[0].query_str == "example"
            assert list_subs[0].destination == -87023
            assert list_subs[0].latest_update == datetime.datetime(2019, 10, 25, 17, 34, 8)
            assert list_subs[1].query_str == "test"
            assert list_subs[1].destination == 87238
            assert list_subs[1].latest_update == datetime.datetime(2019, 10, 26, 18, 57, 9)
        assert len(watcher.blocklists) == 2
        assert 8732 in watcher.blocklists
        assert len(watcher.blocklists[8732]) == 2
        assert isinstance(watcher.blocklists[8732], set)
        assert "example" in watcher.blocklists[8732]
        assert "ych" in watcher.blocklists[8732]
        assert -123 in watcher.blocklists
        assert len(watcher.blocklists[-123]) == 1
        assert isinstance(watcher.blocklists[-123], set)
        assert "fred" in watcher.blocklists[-123]
    finally:
        SubscriptionWatcher.FILENAME = old_filename
        os.remove(test_watcher_file)


def test_to_json_and_back(mock_client):
    test_watcher_file = "./test_subscription_watcher.json"
    if os.path.exists(test_watcher_file):
        os.remove(test_watcher_file)
    old_filename = SubscriptionWatcher.FILENAME
    SubscriptionWatcher.FILENAME = test_watcher_file
    api = MockExportAPI()
    latest_submissions = [
        SubmissionBuilder(submission_id="123243").build_short_submission(),
        SubmissionBuilder(submission_id="123242").build_short_submission(),
        SubmissionBuilder(submission_id="123240").build_short_submission(),
    ]
    subscription1 = Subscription("query", 1234)
    subscription2 = Subscription("example", 5678)
    cache = MockSubmissionCache()
    watcher = SubscriptionWatcher(api, mock_client, cache)
    for submission in latest_submissions[::-1]:
        watcher.update_latest_id(SubmissionID("fa", submission.submission_id))
    watcher.subscriptions.add(subscription1)
    watcher.subscriptions.add(subscription2)
    watcher.blocklists[3452] = {"test", "example"}
    watcher.blocklists[1453] = {"ych"}

    try:
        watcher.save_to_json()
        new_watcher = SubscriptionWatcher.load_from_json(api, mock_client, cache)

        assert len(new_watcher.latest_ids) == 3
        assert "123243" in new_watcher.latest_ids
        assert "123242" in new_watcher.latest_ids
        assert "123240" in new_watcher.latest_ids
        assert list(watcher.latest_ids) == list(new_watcher.latest_ids)
        assert len(new_watcher.subscriptions) == 2
        list_subs = list(new_watcher.subscriptions)
        if list_subs[0].query_str == "query":
            assert list_subs[0].destination == 1234
            assert list_subs[1].query_str == "example"
            assert list_subs[1].destination == 5678
        else:
            assert list_subs[0].query_str == "example"
            assert list_subs[0].destination == 5678
            assert list_subs[1].query_str == "query"
            assert list_subs[1].destination == 1234
        assert len(new_watcher.blocklists) == 2
        assert 3452 in new_watcher.blocklists
        assert len(new_watcher.blocklists[3452]) == 2
        assert isinstance(new_watcher.blocklists[3452], set)
        assert "test" in new_watcher.blocklists[3452]
        assert "example" in new_watcher.blocklists[3452]
        assert 1453 in new_watcher.blocklists
        assert len(new_watcher.blocklists[1453]) == 1
        assert isinstance(new_watcher.blocklists[1453], set)
        assert "ych" in new_watcher.blocklists[1453]
    finally:
        SubscriptionWatcher.FILENAME = old_filename
        os.remove(test_watcher_file)
