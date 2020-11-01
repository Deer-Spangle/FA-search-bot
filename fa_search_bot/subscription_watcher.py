import collections
import datetime
import json
import logging
import os
import time
from typing import List, Optional, Deque, Set, Dict

import dateutil.parser
import heartbeat
import telegram

from fa_search_bot.fa_export_api import FAExportAPI
from fa_search_bot.fa_submission import FASubmissionFull, FASubmissionShort
from fa_search_bot.query_parser import AndQuery, NotQuery, parse_query, Query

heartbeat.heartbeat_app_url = "https://heartbeat.spangle.org.uk/"
heartbeat_app_name = "FASearchBot_sub_thread"

logger = logging.getLogger(__name__)
usage_logger = logging.getLogger("usage")


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
        self.blocklists = dict()  # type: Dict[int, Set[str]]
        self.blocklist_query_cache = dict()  # type: Dict[str, Query]

    def run(self):
        """
        This method is launched as a separate thread, it reads the browse endpoint for new submissions, and checks if they
        match existing subscriptions
        """
        self.running = True
        while self.running:
            try:
                new_results = self._get_new_results()
            except Exception as e:
                logger.error("Failed to get new results", exc_info=e)
                continue
            count = 0
            heartbeat.update_heartbeat(heartbeat_app_name)
            # Check for subscription updates
            for result in new_results:
                count += 1
                # Try and get the full data
                try:
                    full_result = self.api.get_full_submission(result.submission_id)
                    logger.debug("Got full data for submission %s", result.submission_id)
                except Exception:
                    logger.warning("Submission %s, disappeared before I could check it.", result.submission_id)
                    continue
                # Copy subscriptions, to avoid "changed size during iteration" issues
                subscriptions = self.subscriptions.copy()
                # Check which subscriptions match
                matching_subscriptions = []
                for subscription in subscriptions:
                    blocklist = self.blocklists.get(subscription.destination, set())
                    blocklist_query = AndQuery([NotQuery(self._get_blocklist_query(block)) for block in blocklist])
                    if subscription.matches_result(full_result, blocklist_query):
                        matching_subscriptions.append(subscription)
                logger.debug("Submission %s matches %s subscriptions", result.submission_id, len(matching_subscriptions))
                if matching_subscriptions:
                    self._send_updates(matching_subscriptions, full_result)
                # Update latest ids with the submission we just checked, and save config
                self._update_latest_ids([result])
                # If we've done ten, update heartbeat
                if count % self.UPDATE_PER_HEARTBEAT == 0:
                    heartbeat.update_heartbeat(heartbeat_app_name)
                    logger.debug("Heartbeat")
            # Wait
            self._wait_while_running(self.BACK_OFF)

    def stop(self):
        logger.info("Stopping subscription watcher")
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
                logger.warning("Failed to get browse page, retrying", exc_info=e)
                self._wait_while_running(self.BROWSE_RETRY_BACKOFF)

    def _get_new_results(self) -> List[FASubmissionShort]:
        """
        Gets new results since last scan, returning them in order from oldest to newest.
        """
        if len(self.latest_ids) == 0:
            logger.info("First time checking subscriptions, getting initial submissions")
            first_page = self._get_browse_page()
            self._update_latest_ids(first_page[::-1])
            return []
        page = 1
        browse_results = []  # type: List[FASubmissionShort]
        new_results = []  # type: List[FASubmissionShort]
        caught_up = False
        while page <= self.PAGE_CAP and not caught_up:
            logger.info("Getting browse page: %s", page)
            page_results = self._get_browse_page(page)
            browse_results += page_results
            # Get new results
            for result in page_results:
                if result.submission_id in self.latest_ids:
                    caught_up = True
                    break
                new_results.append(result)
            page += 1
        logger.info("New submissions: %s", len(new_results))
        # Return oldest result first
        return new_results[::-1]

    def _update_latest_ids(self, browse_results: List[FASubmissionShort]):
        for result in browse_results:
            self.latest_ids.append(result.submission_id)
        self.save_to_json()

    def _send_updates(self, subscriptions: List['Subscription'], result: FASubmissionFull):
        destination_map = collections.defaultdict(lambda: [])
        for sub in subscriptions:
            sub.latest_update = datetime.datetime.now()
            destination_map[sub.destination].append(sub)
        for dest, subs in destination_map.items():
            queries = ", ".join([f"\"{sub.query_str}\"" for sub in subs])
            prefix = f"Update on {queries} subscription{'' if len(subs) == 1 else 's'}:"
            try:
                logger.info("Sending submission %s to subscription", result.submission_id)
                usage_logger.info("Submission sent to subscription")
                result.send_message(self.bot, dest, prefix=prefix)
            except Exception as e:
                logger.error("Failed to send submission: %s to %s", result.submission_id, dest, exc_info=e)

    def _get_blocklist_query(self, blocklist_str: str) -> Query:
        if blocklist_str not in self.blocklist_query_cache:
            self.blocklist_query_cache[blocklist_str] = parse_query(blocklist_str)
        return self.blocklist_query_cache[blocklist_str]

    def add_to_blocklist(self, destination: int, tag: str):
        # Ensure blocklist query can be parsed without error
        self.blocklist_query_cache[tag] = parse_query(tag)
        # Add to blocklists
        if destination in self.blocklists:
            self.blocklists[destination].add(tag)
        else:
            self.blocklists[destination] = {tag}

    def migrate_chat(self, old_chat_id: int, new_chat_id: int) -> None:
        # Migrate blocklist
        if old_chat_id in self.blocklists:
            for query in self.blocklists[old_chat_id]:
                self.add_to_blocklist(new_chat_id, query)
        # Migrate subscriptions
        for subscription in self.subscriptions:
            if subscription.destination == old_chat_id:
                subscription.destination = new_chat_id
        # Remove old blocklist
        if old_chat_id in self.blocklists:
            del self.blocklists[old_chat_id]
        # Save
        self.save_to_json()

    def save_to_json(self):
        logger.debug("Saving subscriptions data")
        subscriptions = self.subscriptions.copy()
        data = {
            "latest_ids": list(self.latest_ids),
            "subscriptions": [x.to_json() for x in subscriptions],
            "blacklists": {str(k): list(v) for k, v in self.blocklists.items()}
        }
        with open(self.FILENAME_TEMP, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(self.FILENAME_TEMP, self.FILENAME)

    def save_to_json_new(self):
        logger.debug("Saving subscription data in new format")
        destination_dict = collections.defaultdict(lambda: {
            "subscriptions": [],
            "blocks": []
        })
        for subscription in self.subscriptions.copy():
            destination_dict[str(subscription.destination)]["subscriptions"].append(subscription.to_json_new())
        for dest, block_queries in self.blocklists.items():
            for block in block_queries:
                destination_dict[str(dest)]["blocks"].append({"query": block})
        data = {
            "latest_ids": list(self.latest_ids),
            "destinations": destination_dict
        }
        with open(self.FILENAME_TEMP, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(self.FILENAME_TEMP, self.FILENAME)

    @staticmethod
    def load_from_json(api: FAExportAPI, bot: telegram.Bot) -> 'SubscriptionWatcher':
        logger.debug("Loading subscription config from file")
        try:
            with open(SubscriptionWatcher.FILENAME, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.info("No subscription config exists, creating a blank one")
            return SubscriptionWatcher(api, bot)
        new_watcher = SubscriptionWatcher(api, bot)
        for old_id in data["latest_ids"]:
            new_watcher.latest_ids.append(old_id)
        new_watcher.subscriptions = set(Subscription.from_json(x) for x in data["subscriptions"])
        new_watcher.blocklists = {int(k): set(v) for k, v in data["blacklists"].items()}
        return new_watcher

    @staticmethod
    def load_from_json_new(api: FAExportAPI, bot: telegram.Bot) -> 'SubscriptionWatcher':
        logger.debug("Loading subscription config from file in new format")
        try:
            with open(SubscriptionWatcher.FILENAME, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.info("No subscription config exists, creating a blank one")
            return SubscriptionWatcher(api, bot)
        new_watcher = SubscriptionWatcher(api, bot)
        for old_id in data["latest_ids"]:
            new_watcher.latest_ids.append(old_id)
        subscriptions = set()
        for dest, value in data["destinations"].items():
            dest_id = int(dest)
            for subscription in value["subscriptions"]:
                subscriptions.add(Subscription.from_json_new(subscription, dest_id))
            new_watcher.blocklists[dest_id] = set(block["query"] for block in value["blocks"])
        new_watcher.subscriptions = subscriptions
        return new_watcher


class Subscription:

    def __init__(self, query_str: str, destination: int):
        self.query_str = query_str
        self.destination = destination
        self.latest_update = None  # type: Optional[datetime.datetime]
        self.query = parse_query(query_str)

    def matches_result(self, result: FASubmissionFull, blocklist_query: Query) -> bool:
        full_query = AndQuery([self.query, blocklist_query])
        return full_query.matches_submission(result)

    def to_json(self):
        latest_update_str = None
        if self.latest_update is not None:
            latest_update_str = self.latest_update.isoformat()
        return {
            "query": self.query_str,
            "destination": self.destination,
            "latest_update": latest_update_str
        }

    def to_json_new(self):
        latest_update_str = None
        if self.latest_update is not None:
            latest_update_str = self.latest_update.isoformat()
        return {
            "query": self.query_str,
            "latest_update": latest_update_str
        }

    @staticmethod
    def from_json(saved_sub) -> 'Subscription':
        query = saved_sub["query"]
        destination = saved_sub["destination"]
        new_sub = Subscription(query, destination)
        new_sub.latest_update = None
        if saved_sub["latest_update"] is not None:
            new_sub.latest_update = dateutil.parser.parse(saved_sub["latest_update"])
        return new_sub

    @staticmethod
    def from_json_new(saved_sub: Dict, dest_id: int) -> 'Subscription':
        query = saved_sub["query"]
        new_sub = Subscription(query, dest_id)
        new_sub.latest_update = None
        if saved_sub["latest_update"] is not None:
            new_sub.latest_update = dateutil.parser.parse(saved_sub["latest_update"])
        return new_sub

    def __eq__(self, other):
        if not isinstance(other, Subscription):
            return False
        return self.query_str == other.query_str and self.destination == other.destination

    def __hash__(self):
        return hash((self.query_str, self.destination))

    def __str__(self):
        return f"Subscription(destination={self.destination}, query=\"{self.query_str}\")"
