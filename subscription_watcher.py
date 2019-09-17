import collections
import datetime
import time
from typing import List, Optional, Deque

from fa_export_api import FAExportAPI
from fa_submission import FASubmissionFull, FASubmissionShort


class SubscriptionWatcher:
    PAGE_CAP = 10
    BACK_OFF = 20

    def __init__(self, api: FAExportAPI):
        self.api = api
        self.latest_ids = collections.deque(maxlen=15)  # type: Deque[str]
        self.running = False
        self.subscriptions = []  # type: List[Subscription]

    """
    This method is launched as a separate thread, it reads the browse endpoint for new submissions, and checks if they 
    match existing subscriptions
    """
    def run(self):
        self.running = True
        while self.running:
            new_results = self._get_new_results()
            # Check for subscription updates
            for result in new_results[::-1]:
                full_result = self.api.get_full_submission(result.submission_id)
                for subscription in self.subscriptions:
                    if subscription.matches_result(full_result):
                        subscription.send(full_result)
            # Wait
            time.sleep(self.BACK_OFF)

    def _get_new_results(self) -> List[FASubmissionShort]:
        if len(self.latest_ids) == 0:
            first_page = self.api.get_browse_page()
            self._update_latest_ids(first_page)
            return []
        page = 1
        browse_results = []  # type: List[FASubmissionShort]
        new_results = []  # type: List[FASubmissionShort]
        caught_up = False
        while page < self.PAGE_CAP and not caught_up:
            page_results = self.api.get_browse_page(page)
            browse_results += page_results
            # Get new results
            for result in page_results:
                if result.submission_id in self.latest_ids:
                    caught_up = True
                    break
                new_results.append(result)
        self._update_latest_ids(browse_results)
        return new_results

    def _update_latest_ids(self, browse_results: List[FASubmissionShort]):
        for result in browse_results[::-1]:
            self.latest_ids.append(result.submission_id)

    def save(self):
        pass

    def load(self):
        pass


class Subscription:

    def __init__(self, query, destination):
        self.query = query
        self.destination = destination
        self.latest_update = None  # type: Optional[datetime.datetime]

    def matches_result(self, result: FASubmissionFull) -> bool:
        pass  # TODO

    def send(self, result: FASubmissionFull):
        pass  # TODO

    def to_json(self):
        pass  # TODO

    def from_json(self):
        pass  # TODO
