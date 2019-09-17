import datetime
import time
import unittest
from threading import Thread

from fa_submission import FASubmissionFull
from subscription_watcher import SubscriptionWatcher, Subscription
from tests.util.mock_export_api import MockExportAPI, MockSubmission
from tests.util.mock_method import MockMethod


class MockSubscription(Subscription):

    def __init__(self, query, destination):
        super().__init__(query, destination)
        self.submissions_checked = []

    def matches_result(self, result: FASubmissionFull) -> bool:
        self.submissions_checked.append(result)
        return True

    def send(self, result: FASubmissionFull):
        pass


class SubscriptionWatcherTest(unittest.TestCase):

    def test_init(self):
        api = MockExportAPI()
        s = SubscriptionWatcher(api)

        assert s.api == api
        assert len(s.latest_ids) == 0
        assert s.running is False
        assert len(s.subscriptions) == 0

    def watcher_killer(self, watcher: SubscriptionWatcher):
        # Wait until watcher is running
        while watcher.running is False:
            time.sleep(0.1)
        # Stop watcher
        watcher.running = False

    def test_run_is_stopped_by_running_false(self):
        api = MockExportAPI()
        s = SubscriptionWatcher(api)
        # Shorten the wait
        s.BACK_OFF = 1

        thread = Thread(target=lambda: self.watcher_killer(s))
        thread.start()

        # Run watcher
        s.run()

        assert True
        thread.join()

    def test_run_calls_get_new_results(self):
        api = MockExportAPI()
        watcher = SubscriptionWatcher(api)
        method_called = MockMethod([])
        watcher._get_new_results = method_called.call
        # Shorten the wait
        watcher.BACK_OFF = 1

        thread = Thread(target=lambda: self.watcher_killer(watcher))
        thread.start()
        # Run watcher
        watcher.run()
        thread.join()

        assert method_called.called

    def test_run_checks_all_subscriptions(self):
        submission = MockSubmission("12322")
        api = MockExportAPI().with_submission(submission)
        watcher = SubscriptionWatcher(api)
        method_called = MockMethod([MockSubmission])
        watcher._get_new_results = method_called.call
        watcher.BACK_OFF = 1
        sub1 = MockSubscription("deer", 0)
        sub2 = MockSubscription("dog", 0)
        watcher.subscriptions = [sub1, sub2]

        thread = Thread(target=lambda: self.watcher_killer(watcher))
        thread.start()
        # Run watcher
        watcher.run()
        thread.join()

        assert submission in sub1.submissions_checked
        assert submission in sub2.submissions_checked
        assert method_called.called

    def test_run_checks_all_new_results(self):
        submission1 = MockSubmission("12322")
        submission2 = MockSubmission("12324")
        api = MockExportAPI().with_submissions([submission1, submission2])
        watcher = SubscriptionWatcher(api)
        method_called = MockMethod([MockSubmission])
        watcher._get_new_results = method_called.call
        watcher.BACK_OFF = 1
        sub = MockSubscription("deer", 0)
        watcher.subscriptions = [sub]

        thread = Thread(target=lambda: self.watcher_killer(watcher))
        thread.start()
        # Run watcher
        watcher.run()
        thread.join()

        assert submission1 in sub.submissions_checked
        assert submission2 in sub.submissions_checked
        assert method_called.called

    def test_run_sleeps_backoff_time(self):
        api = MockExportAPI()
        s = SubscriptionWatcher(api)
        # Shorten the wait
        s.BACK_OFF = 3

        thread = Thread(target=lambda: self.watcher_killer(s))
        thread.start()

        # Run watcher
        start_time = datetime.datetime.now()
        s.run()
        end_time = datetime.datetime.now()
        thread.join()

        time_waited = end_time - start_time
        assert 3 <= time_waited.seconds <= 5

    def test_get_new_results_handles_empty_latest_ids(self):
        assert False
        pass  # TODO

    def test_get_new_results_updates_latest_ids(self):
        assert False
        pass  # TODO

    def test_get_new_results_updates_latest_ids_after_checking_two_pages(self):
        assert False
        pass  # TODO

    def test_get_new_results_returns_new_results(self):
        assert False
        pass  # TODO

    def test_get_new_results_goes_to_another_page(self):
        assert False
        pass  # TODO

    def test_get_new_results_respects_page_cap(self):
        assert False
        pass  # TODO

    def test_update_latest_ids(self):
        assert False
        pass  # TODO

    def test_to_json(self):
        assert False
        pass  # TODO

    def test_from_json(self):
        assert False
        pass  # TODO

    def test_to_json_and_back(self):
        assert False
        pass  # TODO
