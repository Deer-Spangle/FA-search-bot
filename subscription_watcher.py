import collections
import datetime
import json
import os
import re
import string
import time
from typing import List, Optional, Deque, Set, Dict
import dateutil.parser
import telegram
import heartbeat

from fa_export_api import FAExportAPI
from fa_submission import FASubmissionFull, FASubmissionShort

heartbeat.heartbeat_app_url = "https://heartbeat.spangle.org.uk/"
heartbeat_app_name = "FASearchBot_sub_thread"


class SubscriptionWatcher:
    PAGE_CAP = 900
    BACK_OFF = 20
    BROWSE_RETRY_BACKOFF = 20
    UPDATE_PER_HEARTBEAT = 10
    FILENAME = "subscriptions.json"
    FILENAME_TEMP = "subscriptions.temp.json"

    def __init__(self, api: FAExportAPI, bot: telegram.Bot):
        self.api = api
        self.bot = bot
        self.latest_ids = collections.deque(maxlen=15)  # type: Deque[str]
        self.running = False
        self.subscriptions = set()  # type: Set[Subscription]
        self.blacklists = dict()  # type: Dict[int, Set[str]]

    """
    This method is launched as a separate thread, it reads the browse endpoint for new submissions, and checks if they 
    match existing subscriptions
    """
    def run(self):
        self.running = True
        while self.running:
            try:
                new_results = self._get_new_results()
            except Exception as e:
                print(f"Failed to get new results because {e}")
                continue
            count = 0
            heartbeat.update_heartbeat(heartbeat_app_name)
            # Check for subscription updates
            for result in new_results:
                count += 1
                # Try and get the full data
                try:
                    full_result = self.api.get_full_submission(result.submission_id)
                except Exception:
                    print(f"Submission {result.submission_id} disappeared before I could check it.")
                    continue
                # Copy subscriptions, to avoid "changed size during iteration" issues
                subscriptions = self.subscriptions.copy()
                # Check which subscriptions match
                for subscription in subscriptions:
                    blacklist = self.blacklists.get(subscription.destination, set())
                    if subscription.matches_result(full_result, blacklist):
                        try:
                            self._send_update(subscription, full_result)
                        except Exception as e:
                            print(f"Failed to send submission: {full_result.submission_id} "
                                  f"to {subscription.destination} because {e}.")
                # Update latest ids with the submission we just checked, and save config
                self._update_latest_ids([result])
                # If we've done ten, update heartbeat
                if count % self.UPDATE_PER_HEARTBEAT == 0:
                    heartbeat.update_heartbeat(heartbeat_app_name)
            # Wait
            self._wait_while_running(self.BACK_OFF)

    def stop(self):
        self.running = False

    def _wait_while_running(self, seconds):
        sleep_end = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        while datetime.datetime.now() < sleep_end:
            if not self.running:
                break
            time.sleep(0.1)

    def _get_browse_page(self, page: int = 1) -> List[FASubmissionShort]:
        while self.running:
            try:
                return self.api.get_browse_page(page)
            except ValueError as e:
                self._wait_while_running(self.BROWSE_RETRY_BACKOFF)

    def _get_new_results(self) -> List[FASubmissionShort]:
        """
        Gets new results since last scan, returning them in order from oldest to newest.
        """
        if len(self.latest_ids) == 0:
            first_page = self._get_browse_page()
            self._update_latest_ids(first_page[::-1])
            return []
        page = 1
        browse_results = []  # type: List[FASubmissionShort]
        new_results = []  # type: List[FASubmissionShort]
        caught_up = False
        while page <= self.PAGE_CAP and not caught_up:
            page_results = self._get_browse_page(page)
            browse_results += page_results
            # Get new results
            for result in page_results:
                if result.submission_id in self.latest_ids:
                    caught_up = True
                    break
                new_results.append(result)
            page += 1
        # Return oldest result first
        return new_results[::-1]

    def _update_latest_ids(self, browse_results: List[FASubmissionShort]):
        for result in browse_results:
            self.latest_ids.append(result.submission_id)
        self.save_to_json()

    def _send_update(self, subscription: 'Subscription', result: FASubmissionFull):
        subscription.latest_update = datetime.datetime.now()
        result.send_message(self.bot, subscription.destination, prefix=f"Update on \"{subscription.query}\" subscription:")

    def add_to_blacklist(self, destination: int, tag: str):
        if destination in self.blacklists:
            self.blacklists[destination].add(tag)
        else:
            self.blacklists[destination] = {tag}

    def save_to_json(self):
        subscriptions = self.subscriptions.copy()
        data = {
            "latest_ids": list(self.latest_ids),
            "subscriptions": [x.to_json() for x in subscriptions],
            "blacklists": {str(k): list(v) for k, v in self.blacklists.items()}
        }
        with open(self.FILENAME_TEMP, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(self.FILENAME_TEMP, self.FILENAME)

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
        new_watcher.blacklists = {int(k): set(v) for k, v in data["blacklists"].items()}
        return new_watcher


class Subscription:

    def __init__(self, query: str, destination: int):
        self.query = query
        self.destination = destination
        self.latest_update = None  # type: Optional[datetime.datetime]

    def matches_result(self, result: FASubmissionFull, blacklist: Set[str]) -> bool:
        query_words = self.query.lower().split()
        all_text = \
            self._split_text_to_words(result.title) + \
            self._split_text_to_words(result.description) + \
            result.keywords
        positive_words = [x for x in query_words if x[0] != "-"]
        negative_words = [x[1:] for x in query_words if x[0] == "-"]
        negative_words += list(blacklist)
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
