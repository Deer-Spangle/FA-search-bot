import collections
import datetime
import json
import os
import time
from threading import Thread
from typing import List

from unittest.mock import patch
import telegram

from fa_search_bot.fa_submission import FASubmissionFull
from fa_search_bot.query_parser import AndQuery, NotQuery, WordQuery
from fa_search_bot.subscription_watcher import SubscriptionWatcher, Subscription
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_method import MockMethod
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder


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
def watcher_killer(watcher: SubscriptionWatcher):
    # Wait until watcher is running
    while watcher.running is False:
        time.sleep(0.1)
    # Stop watcher
    watcher.running = False


@patch.object(telegram, "Bot")
def test_init(bot):
    api = MockExportAPI()
    s = SubscriptionWatcher(api, bot)

    assert s.api == api
    assert len(s.latest_ids) == 0
    assert s.running is False
    assert len(s.subscriptions) == 0


@patch.object(telegram, "Bot")
def test_run__is_stopped_by_running_false(bot):
    api = MockExportAPI()
    s = SubscriptionWatcher(api, bot)
    # Shorten the wait
    s.BACK_OFF = 1

    thread = Thread(target=lambda: watcher_killer(s))
    thread.start()

    # Run watcher
    s.run()

    assert True
    thread.join()


@patch.object(telegram, "Bot")
def test_run__calls_get_new_results(bot):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, bot)
    method_called = MockMethod([])
    watcher._get_new_results = method_called.call
    # Shorten the wait
    watcher.BACK_OFF = 1

    thread = Thread(target=lambda: watcher_killer(watcher))
    thread.start()
    # Run watcher
    watcher.run()
    thread.join()

    assert method_called.called


@patch.object(telegram, "Bot")
def test_run__calls_update_latest_ids(bot):
    submission1 = MockSubmission("12322")
    submission2 = MockSubmission("12324")
    api = MockExportAPI().with_submissions([submission1, submission2])
    watcher = SubscriptionWatcher(api, bot)
    mock_new_results = MockMethod([submission1, submission2])
    watcher._get_new_results = mock_new_results.call
    mock_update_latest = MockMethod()
    watcher._update_latest_ids = mock_update_latest.call
    # Shorten the wait
    watcher.BACK_OFF = 1

    thread = Thread(target=lambda: watcher_killer(watcher))
    thread.start()
    # Run watcher
    watcher.run()
    thread.join()

    assert mock_update_latest.called
    assert mock_update_latest.args[0] == [submission2]


@patch.object(telegram, "Bot")
def test_run__updates_latest_ids(bot):
    submission1 = MockSubmission("12322")
    submission2 = MockSubmission("12324")
    api = MockExportAPI().with_submissions([submission1, submission2])
    watcher = SubscriptionWatcher(api, bot)
    mock_new_results = MockMethod([submission1, submission2])
    watcher._get_new_results = mock_new_results.call
    mock_save_json = MockMethod()
    watcher.save_to_json = mock_save_json.call
    # Shorten the wait
    watcher.BACK_OFF = 1

    thread = Thread(target=lambda: watcher_killer(watcher))
    thread.start()
    # Run watcher
    watcher.run()
    thread.join()

    assert mock_save_json.called
    assert submission1.submission_id in watcher.latest_ids
    assert submission2.submission_id in watcher.latest_ids


@patch.object(telegram, "Bot")
def test_run__checks_all_subscriptions(bot):
    submission = MockSubmission("12322")
    api = MockExportAPI().with_submission(submission)
    watcher = SubscriptionWatcher(api, bot)
    method_called = MockMethod([submission])
    watcher._get_new_results = method_called.call
    watcher.BACK_OFF = 1
    sub1 = MockSubscription("deer", 0)
    sub2 = MockSubscription("dog", 0)
    watcher.subscriptions = [sub1, sub2]

    thread = Thread(target=lambda: watcher_killer(watcher))
    thread.start()
    # Run watcher
    watcher.run()
    thread.join()

    assert submission in sub1.submissions_checked
    assert submission in sub2.submissions_checked
    assert method_called.called


@patch.object(telegram, "Bot")
def test_run__checks_all_new_results(bot):
    submission1 = MockSubmission("12322")
    submission2 = MockSubmission("12324")
    api = MockExportAPI().with_submissions([submission1, submission2])
    watcher = SubscriptionWatcher(api, bot)
    method_called = MockMethod([submission1, submission2])
    watcher._get_new_results = method_called.call
    watcher.BACK_OFF = 1
    sub = MockSubscription("deer", 0)
    watcher.subscriptions = [sub]

    thread = Thread(target=lambda: watcher_killer(watcher))
    thread.start()
    # Run watcher
    watcher.run()
    thread.join()

    assert submission1 in sub.submissions_checked
    assert submission2 in sub.submissions_checked
    assert method_called.called


@patch.object(telegram, "Bot")
def test_run__sleeps_backoff_time(bot):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, bot)
    # Shorten the wait
    watcher.BACK_OFF = 3

    api.call_after_x_browse = (lambda: watcher.stop(), 2)

    # Run watcher
    start_time = datetime.datetime.now()
    watcher.run()
    end_time = datetime.datetime.now()

    time_waited = end_time - start_time
    assert 3 <= time_waited.seconds <= 5


@patch.object(telegram, "Bot")
def test_run__can_exit_fast(bot):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, bot)
    # Shorten the wait
    watcher.BACK_OFF = 3

    thread = Thread(target=lambda: watcher_killer(watcher))
    thread.start()

    # Run watcher
    start_time = datetime.datetime.now()
    watcher.run()
    end_time = datetime.datetime.now()
    thread.join()

    time_waited = end_time - start_time
    assert time_waited.seconds <= 1


@patch.object(telegram, "Bot")
def test_run__failed_to_send_doesnt_kill_watcher(bot):
    submission = MockSubmission("12322")
    api = MockExportAPI().with_browse_results([submission], 1)
    watcher = SubscriptionWatcher(api, bot)
    submission.send_message = lambda *args: (_ for _ in ()).throw(Exception)
    watcher.BACK_OFF = 3
    sub1 = MockSubscription("deer", 0)
    watcher.subscriptions = [sub1]

    api.call_after_x_browse = (lambda: watcher.stop(), 2)
    # Run watcher
    start_time = datetime.datetime.now()
    watcher.run()
    end_time = datetime.datetime.now()

    time_waited = end_time - start_time
    assert 3 <= time_waited.seconds <= 5


@patch.object(telegram, "Bot")
def test_run__passes_correct_blocklists_to_subscriptions(bot):
    submission = MockSubmission("12322")
    api = MockExportAPI().with_submission(submission)
    watcher = SubscriptionWatcher(api, bot)
    method_called = MockMethod([submission])
    watcher._get_new_results = method_called.call
    watcher.BACK_OFF = 1
    watcher.blocklists = {
        156: {"test", "ych"},
        -200: {"example"}
    }
    sub1 = MockSubscription("deer", 156)
    sub2 = MockSubscription("dog", -232)
    watcher.subscriptions = [sub1, sub2]

    thread = Thread(target=lambda: watcher_killer(watcher))
    thread.start()
    # Run watcher
    watcher.run()
    thread.join()

    assert submission in sub1.submissions_checked
    assert len(sub1.blocklists) == 1
    assert sub1.blocklists[0] in [
        AndQuery([NotQuery(WordQuery("test")), NotQuery(WordQuery("ych"))]),
        AndQuery([NotQuery(WordQuery("ych")), NotQuery(WordQuery("test"))])
    ]
    assert submission in sub2.submissions_checked
    assert len(sub2.blocklists) == 1
    assert sub2.blocklists[0] == AndQuery([])
    assert method_called.called


@patch.object(telegram, "Bot")
def test_get_new_results__handles_empty_latest_ids(bot):
    api = MockExportAPI()
    api.with_browse_results([MockSubmission("1223"), MockSubmission("1222"), MockSubmission("1220")])
    watcher = SubscriptionWatcher(api, bot)
    watcher.running = True

    results = watcher._get_new_results()

    assert len(results) == 0
    assert len(watcher.latest_ids) == 3
    assert watcher.latest_ids[0] == "1220"
    assert watcher.latest_ids[1] == "1222"
    assert watcher.latest_ids[2] == "1223"


@patch.object(telegram, "Bot")
def test_get_new_results__returns_new_results(bot):
    api = MockExportAPI()
    api.with_browse_results([MockSubmission("1223"), MockSubmission("1222"), MockSubmission("1220")])
    watcher = SubscriptionWatcher(api, bot)
    watcher.latest_ids.append("1220")
    watcher.running = True

    results = watcher._get_new_results()

    assert len(results) == 2
    assert results[0].submission_id == "1222"
    assert results[1].submission_id == "1223"


@patch.object(telegram, "Bot")
def test_get_new_results__goes_to_another_page(bot):
    api = MockExportAPI()
    api.with_browse_results([MockSubmission("1227"), MockSubmission("1225"), MockSubmission("1224")], page=1)
    api.with_browse_results([MockSubmission("1223"), MockSubmission("1222"), MockSubmission("1220")], page=2)
    watcher = SubscriptionWatcher(api, bot)
    watcher.latest_ids = collections.deque(maxlen=4)
    watcher.latest_ids.append("1220")
    watcher.running = True

    results = watcher._get_new_results()

    assert len(results) == 5
    assert results[0].submission_id == "1222"
    assert results[1].submission_id == "1223"
    assert results[2].submission_id == "1224"
    assert results[3].submission_id == "1225"
    assert results[4].submission_id == "1227"


@patch.object(telegram, "Bot")
def test_get_new_results__respects_page_cap(bot):
    api = MockExportAPI()
    api.with_browse_results([MockSubmission("1300")], page=1)
    api.with_browse_results([MockSubmission("1298")], page=2)
    api.with_browse_results([MockSubmission("1297")], page=3)
    api.with_browse_results([MockSubmission("1295")], page=4)
    api.with_browse_results([MockSubmission("1280")], page=5)
    api.with_browse_results([MockSubmission("1272")], page=6)
    api.with_browse_results([MockSubmission("1250")], page=7)
    watcher = SubscriptionWatcher(api, bot)
    watcher.PAGE_CAP = 5
    watcher.latest_ids.append("1250")
    watcher.running = True

    results = watcher._get_new_results()

    assert len(results) == 5
    assert "1272" not in [x.submission_id for x in results]


@patch.object(telegram, "Bot")
def test_update_latest_ids(bot):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, bot)
    id_list = ["1234", "1233", "1230", "1229"]
    submissions = [MockSubmission(x) for x in id_list]
    mock_save_json = MockMethod()
    watcher.save_to_json = mock_save_json.call

    watcher._update_latest_ids(submissions)

    assert list(watcher.latest_ids) == id_list
    assert mock_save_json.called


@patch.object(telegram, "Bot")
def test_send_updates__sends_message(bot):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, bot)
    subscription = Subscription("test", 12345)
    submission = SubmissionBuilder().build_mock_submission()

    watcher._send_updates([subscription], submission)

    assert submission.send_message.asset_called_once()
    args, kwargs = submission.send_message.call_args
    assert args[0] == bot
    assert args[1] == 12345
    assert "update" in kwargs['prefix'].lower()
    assert "\"test\"" in kwargs['prefix']
    assert "subscription" in kwargs['prefix'].lower()


@patch.object(telegram, "Bot")
def test_send_updates__gathers_subscriptions(bot):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, bot)
    subscription1 = Subscription("test", 12345)
    subscription2 = Subscription("test2", 12345)
    subscription3 = Subscription("test", 54321)
    submission = SubmissionBuilder().build_mock_submission()

    watcher._send_updates([subscription1, subscription2, subscription3], submission)

    assert submission.send_message.call_count == 2
    call_list = submission.send_message.call_args_list
    # Indifferent to call order, so figure out the order here
    call1 = call_list[0]
    call2 = call_list[1]
    if call1[0][1] != 12345:
        call1 = call_list[1]
        call2 = call_list[0]
    args1, kwargs1 = call1
    args2, kwargs2 = call2
    # Check call matching two subscriptions
    assert args1[0] == bot
    assert args2[0] == bot
    assert args1[1] == 12345
    assert args2[1] == 54321
    assert "update" in kwargs1['prefix'].lower()
    assert "\"test\", \"test2\"" in kwargs1['prefix']
    assert "subscriptions:" in kwargs1['prefix'].lower()
    # And check the one subscription call
    assert "update" in kwargs2['prefix'].lower()
    assert "\"test\"" in kwargs2['prefix']
    assert "subscription:" in kwargs2['prefix'].lower()


@patch.object(telegram, "Bot")
def test_send_updates__updates_latest(bot):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, bot)
    subscription = Subscription("test", 12345)
    submission = SubmissionBuilder().build_mock_submission()

    watcher._send_updates([subscription], submission)

    assert subscription.latest_update is not None


@patch.object(telegram, "Bot")
def test_add_to_blocklist__new_blocklist(bot):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, bot)

    watcher.add_to_blocklist(18749, "test")

    assert len(watcher.blocklists[18749]) == 1
    assert isinstance(watcher.blocklists[18749], set)
    assert watcher.blocklists[18749] == {"test"}


@patch.object(telegram, "Bot")
def test_add_to_blocklist__append_blocklist(bot):
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, bot)
    watcher.blocklists[18749] = {"example"}

    watcher.add_to_blocklist(18749, "test")

    assert len(watcher.blocklists[18749]) == 2
    assert isinstance(watcher.blocklists[18749], set)
    assert watcher.blocklists[18749] == {"test", "example"}


@patch.object(telegram, "Bot")
def test_migrate_no_block_queries(bot):
    old_chat_id = 12345
    new_chat_id = 54321
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, bot)
    watcher.subscriptions.add(MockSubscription("ych", old_chat_id))

    watcher.migrate_chat(old_chat_id, new_chat_id)

    assert len(watcher.subscriptions) == 1
    sub = list(watcher.subscriptions)[0]
    assert sub.query_str == "ych"
    assert sub.destination == new_chat_id


@patch.object(telegram, "Bot")
def test_migrate_with_block_queries(bot):
    old_chat_id = 12345
    new_chat_id = 54321
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, bot)
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


@patch.object(telegram, "Bot")
def test_migrate_nothing_matching(bot):
    old_chat_id = 12345
    new_chat_id = 54321
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, bot)
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


@patch.object(telegram, "Bot")
def test_migrate_merge_blocklists(bot):
    old_chat_id = 12345
    new_chat_id = 54321
    api = MockExportAPI()
    watcher = SubscriptionWatcher(api, bot)
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


@patch.object(telegram, "Bot")
def test_save_to_json(bot):
    test_watcher_file = "./test_subscription_watcher.json"
    if os.path.exists(test_watcher_file):
        os.remove(test_watcher_file)
    api = MockExportAPI()
    latest_submissions = [
        SubmissionBuilder(submission_id="123243").build_short_submission(),
        SubmissionBuilder(submission_id="123242").build_short_submission(),
        SubmissionBuilder(submission_id="123240").build_short_submission()
    ]
    subscription1 = Subscription("query", 1234)
    subscription2 = Subscription("example", 5678)
    watcher = SubscriptionWatcher(api, bot)
    watcher._update_latest_ids(latest_submissions)
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
        assert len(data['latest_ids']) == 3
        assert "123240" in data['latest_ids']
        assert "123242" in data['latest_ids']
        assert "123243" in data['latest_ids']
        assert len(data['subscriptions']) == 2
        if data['subscriptions'][0]['query'] == "query":
            assert data['subscriptions'][0]['destination'] == 1234
            assert data['subscriptions'][1]['query'] == "example"
            assert data['subscriptions'][1]['destination'] == 5678
        else:
            assert data['subscriptions'][0]['query'] == "example"
            assert data['subscriptions'][0]['destination'] == 5678
            assert data['subscriptions'][1]['query'] == "query"
            assert data['subscriptions'][1]['destination'] == 1234
        assert len(data["blacklists"]) == 2
        assert "3452" in data["blacklists"]
        assert len(data["blacklists"]["3452"]) == 2
        assert isinstance(data["blacklists"]["3452"], list)
        assert "test" in data["blacklists"]["3452"]
        assert "example" in data["blacklists"]["3452"]
        assert "1453" in data["blacklists"]
        assert len(data["blacklists"]["1453"]) == 1
        assert isinstance(data["blacklists"]["1453"], list)
        assert data["blacklists"]["1453"] == ["ych"]
    finally:
        os.remove(test_watcher_file)


@patch.object(telegram, "Bot")
def test_from_json(bot):
    test_watcher_file = "./test_subscription_watcher.json"
    if os.path.exists(test_watcher_file):
        os.remove(test_watcher_file)
    old_filename = SubscriptionWatcher.FILENAME
    SubscriptionWatcher.FILENAME = test_watcher_file
    try:
        data = {
            "latest_ids": ["12423", "12422", "12420"],
            "subscriptions": [
                {
                    "query": "test",
                    "destination": 87238,
                    "latest_update": "2019-10-26T18:57:09"
                },
                {
                    "query": "example",
                    "destination": -87023,
                    "latest_update": "2019-10-25T17:34:08"
                }
            ],
            "blacklists": {
                "8732": ["example", "ych"],
                "-123": ["fred"]
            }
        }
        with open(test_watcher_file, "w+") as f:
            json.dump(data, f)
        api = MockExportAPI()

        watcher = SubscriptionWatcher.load_from_json(api, bot)

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


@patch.object(telegram, "Bot")
def test_to_json_and_back(bot):
    test_watcher_file = "./test_subscription_watcher.json"
    if os.path.exists(test_watcher_file):
        os.remove(test_watcher_file)
    old_filename = SubscriptionWatcher.FILENAME
    SubscriptionWatcher.FILENAME = test_watcher_file
    api = MockExportAPI()
    latest_submissions = [
        SubmissionBuilder(submission_id="123243").build_short_submission(),
        SubmissionBuilder(submission_id="123242").build_short_submission(),
        SubmissionBuilder(submission_id="123240").build_short_submission()
    ]
    subscription1 = Subscription("query", 1234)
    subscription2 = Subscription("example", 5678)
    watcher = SubscriptionWatcher(api, bot)
    watcher._update_latest_ids(latest_submissions)
    watcher.subscriptions.add(subscription1)
    watcher.subscriptions.add(subscription2)
    watcher.blocklists[3452] = {"test", "example"}
    watcher.blocklists[1453] = {"ych"}

    try:
        watcher.save_to_json()
        new_watcher = SubscriptionWatcher.load_from_json(api, bot)

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
