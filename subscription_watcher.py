import collections
import datetime
import json
import re
import string
import time
from typing import List, Optional, Deque, Set, Dict
import dateutil.parser
import telegram

from fa_export_api import FAExportAPI
from fa_submission import FASubmissionFull, FASubmissionShort


class SubscriptionWatcher:
    PAGE_CAP = 10
    BACK_OFF = 20
    FILENAME = "subscriptions.json"

    def __init__(self, api: FAExportAPI, bot: telegram.Bot):
        self.api = api
        self.bot = bot
        self.latest_ids = collections.deque(maxlen=15)  # type: Deque[str]
        self.running = False
        self.subscriptions = set()  # type: Set[Subscription]
        self.blacklists = dict()  # type: Dict[int, List[str]]

    """
    This method is launched as a separate thread, it reads the browse endpoint for new submissions, and checks if they 
    match existing subscriptions
    """
    def run(self):
        self.running = True
        while self.running:
            new_results = self._get_new_results()
            # Check for subscription updates
            for result in new_results:
                # Try and get the full data
                try:
                    full_result = self.api.get_full_submission(result.submission_id)
                except Exception:
                    print(f"Submission {result.submission_id} disappeared before I could check it.")
                    continue
                # Check which subscriptions match
                for subscription in self.subscriptions:
                    blacklist = self.blacklists.get(subscription.destination, [])
                    if subscription.matches_result(full_result, blacklist):
                        try:
                            self._send_update(subscription, full_result)
                        except Exception as e:
                            print(f"Failed to send submission: {full_result.submission_id} "
                                  f"to {subscription.destination} because {e}.")
            # Save config
            self.save_to_json()
            # Wait
            time.sleep(self.BACK_OFF)

    def _get_new_results(self) -> List[FASubmissionShort]:
        """
        Gets new results since last scan, returning them in order from oldest to newest.
        """
        if len(self.latest_ids) == 0:
            first_page = self.api.get_browse_page()
            self._update_latest_ids(first_page)
            return []
        page = 1
        browse_results = []  # type: List[FASubmissionShort]
        new_results = []  # type: List[FASubmissionShort]
        caught_up = False
        while page <= self.PAGE_CAP and not caught_up:
            page_results = self.api.get_browse_page(page)
            browse_results += page_results
            # Get new results
            for result in page_results:
                if result.submission_id in self.latest_ids:
                    caught_up = True
                    break
                new_results.append(result)
            page += 1
        self._update_latest_ids(browse_results)
        # Return oldest result first
        return new_results[::-1]

    def _update_latest_ids(self, browse_results: List[FASubmissionShort]):
        for result in browse_results[::-1]:
            self.latest_ids.append(result.submission_id)

    def _send_update(self, subscription: 'Subscription', result: FASubmissionFull):
        self.bot.send_message(
            chat_id=subscription.destination,
            text=f"Update on \"{subscription.query}\" subscription:"
        )
        subscription.latest_update = datetime.datetime.now()
        result.send_message(self.bot, subscription.destination)

    def save_to_json(self):
        data = {
            "latest_ids": list(self.latest_ids),
            "subscriptions": [x.to_json() for x in self.subscriptions],
            "blacklists": {str(k): v for k, v in self.blacklists.items()}
        }
        with open(self.FILENAME, "w") as f:
            json.dump(data, f)

    @staticmethod
    def load_from_json(api: FAExportAPI, bot: telegram.Bot) -> 'SubscriptionWatcher':
        try:
            with open(SubscriptionWatcher.FILENAME, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            return SubscriptionWatcher(api, bot)
        new_watcher = SubscriptionWatcher(api, bot)
        for old_id in data["latest_ids"]:
            new_watcher.latest_ids.append(old_id)
        new_watcher.subscriptions = set(Subscription.from_json(x) for x in data["subscriptions"])
        new_watcher.blacklists = {int(k): v for k, v in data["blacklists"].items()}
        return new_watcher


class Subscription:

    def __init__(self, query: str, destination: int):
        self.query = query
        self.destination = destination
        self.latest_update = None  # type: Optional[datetime.datetime]

    def matches_result(self, result: FASubmissionFull, blacklist: List[str]) -> bool:
        query_words = self.query.lower().split()
        all_text = \
            self._split_text_to_words(result.title) + \
            self._split_text_to_words(result.description) + \
            result.keywords
        positive_words = [x for x in query_words if x[0] != "-"]
        negative_words = [x[1:] for x in query_words if x[0] == "-"]
        negative_words += blacklist
        return all(
            [
                self._query_word_matches_text(word, all_text)
                for word in positive_words
            ]
        ) and not any(
            [
                self._query_word_matches_text(word, all_text)
                for word in negative_words
            ]
        )
    
    def _split_text_to_words(self, text: str) -> List[str]:
        return re.split(r"[\s\"<>]+", text)

    def _query_word_matches_text(self, query_word: str, text: List[str]) -> bool:
        clean_list = [x.lower().strip(string.punctuation) for x in text]
        return query_word in clean_list

    def to_json(self):
        latest_update_str = None
        if self.latest_update is not None:
            latest_update_str = self.latest_update.isoformat()
        return {
            "query": self.query,
            "destination": self.destination,
            "latest_update": latest_update_str
        }

    @staticmethod
    def from_json(saved_sub) -> 'Subscription':
        query = saved_sub["query"]
        destination = saved_sub["destination"]
        new_sub = Subscription(query, destination)
        new_sub.latest_update = saved_sub["latest_update"]
        if new_sub.latest_update is not None:
            new_sub.latest_update = dateutil.parser.parse(new_sub.latest_update)
        return new_sub

    def __eq__(self, other):
        if not isinstance(other, Subscription):
            return False
        return self.query == other.query and self.destination == other.destination

    def __hash__(self):
        return hash((self.query, self.destination))

    def __str__(self):
        return f"Subscription(destination={self.destination}, query=\"{self.query}\")"
