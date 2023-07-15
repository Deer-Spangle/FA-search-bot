from __future__ import annotations

import asyncio
import collections
import json
import logging
import os
from asyncio import Queue, Task
from typing import TYPE_CHECKING

import heartbeat
from prometheus_client import Gauge
from prometheus_client.metrics import Counter

from fa_search_bot.query_parser import AndQuery, NotQuery, parse_query
from fa_search_bot.sites.furaffinity.fa_export_api import CloudflareError, PageNotFound
from fa_search_bot.sites.furaffinity.sendable import SendableFASubmission
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.subscriptions.data_fetcher import DataFetcher
from fa_search_bot.subscriptions.media_fetcher import MediaFetcher
from fa_search_bot.subscriptions.sender import Sender
from fa_search_bot.subscriptions.sub_id_gatherer import SubIDGatherer
from fa_search_bot.subscriptions.subscription import Subscription
from fa_search_bot.subscriptions.utils import time_taken
from fa_search_bot.subscriptions.wait_pool import WaitPool

if TYPE_CHECKING:
    from typing import Deque, Dict, List, Optional, Set

    from telethon import TelegramClient

    from fa_search_bot.query_parser import Query
    from fa_search_bot.sites.furaffinity.fa_export_api import FAExportAPI
    from fa_search_bot.sites.furaffinity.fa_submission import FASubmissionFull
    from fa_search_bot.submission_cache import SubmissionCache

logger = logging.getLogger(__name__)
subs_processed = Counter(
    "fasearchbot_fasubwatcher_submissions_total",
    "Total number of submissions processed by the subscription watcher",
)
latest_sub_processed = Gauge(
    "fasearchbot_fasubwatcher_latest_processed_unixtime",
    "Time that the latest submission was processed",
)
gauge_sub = Gauge("fasearchbot_fasubwatcher_subscription_count", "Total number of subscriptions")
gauge_subs_active = Gauge(
    "fasearchbot_fasubwatcher_subscription_count_active",
    "Number of active subscriptions",
)
gauge_sub_destinations = Gauge(
    "fasearchbot_fasubwatcher_subscription_destination_count",
    "Number of different subscription destinations",
)
gauge_sub_active_destinations = Gauge(
    "fasearchbot_fasubwatcher_subscription_destination_count_active",
    "Number of different subscription destinations with at least one active subscription",
)
gauge_sub_blocks = Gauge(
    "fasearchbot_fasubwatcher_subscription_block_query_count",
    "Total number of blocklist queries",
)
gauge_backlog = Gauge(
    "fasearchbot_fasubwatcher_backlog",
    "Length of the latest list of new submissions to check",
)


class SubscriptionWatcher:
    BACK_OFF = 20
    FILENAME = "subscriptions.json"
    FILENAME_TEMP = "subscriptions.temp.json"
    DATA_FETCHER_POOL_SIZE = 2
    MEDIA_FETCHER_POOL_SIZE = 2

    def __init__(self, api: FAExportAPI, client: TelegramClient, submission_cache: SubmissionCache):
        self.api = api
        self.client = client
        self.submission_cache = submission_cache
        self.latest_ids = collections.deque(maxlen=15)  # type: Deque[str]
        self.running = False
        self.subscriptions = set()  # type: Set[Subscription]
        self.blocklists = dict()  # type: Dict[int, Set[str]]
        self.blocklist_query_cache = dict()  # type: Dict[str, Query]
        gauge_sub.set_function(lambda: len(self.subscriptions))
        gauge_subs_active.set_function(lambda: len([s for s in self.subscriptions if not s.paused]))
        gauge_sub_destinations.set_function(lambda: len(set(s.destination for s in self.subscriptions)))
        gauge_sub_active_destinations.set_function(
            lambda: len(set(s.destination for s in self.subscriptions if not s.paused))
        )
        gauge_sub_blocks.set_function(lambda: sum(len(blocks) for blocks in self.blocklists.values()))
        # TODO: document, instrument
        self.wait_pool = WaitPool()
        self.fetch_data_queue: Queue[SubmissionID] = Queue()
        self.upload_queue: Queue[FASubmissionFull] = Queue()
        self.sub_id_gatherer: Optional[SubIDGatherer] = None
        self.data_fetchers: List[DataFetcher] = []
        self.media_fetchers: List[MediaFetcher] = []
        self.sender: Optional[Sender] = None
        self.sub_tasks: List[Task] = []

    async def start_tasks(self) -> None:
        # TODO: Pull all these out into separate classes please, along with their helper methods
        if self.running or self.sub_tasks:
            raise ValueError("Already running")
        self.running = True
        event_loop = asyncio.get_event_loop()
        # Start the submission ID gatherer
        self.sub_id_gatherer = SubIDGatherer(self)
        sub_id_gatherer_task = event_loop.create_task(self.sub_id_gatherer.run())
        self.sub_tasks.append(sub_id_gatherer_task)
        # Start the data fetchers
        for _ in range(self.DATA_FETCHER_POOL_SIZE):
            data_fetcher = DataFetcher(self)
            self.data_fetchers.append(data_fetcher)
            data_fetcher_task = event_loop.create_task(data_fetcher.run())
            self.sub_tasks.append(data_fetcher_task)
        # Start the media fetchers
        for _ in range(self.MEDIA_FETCHER_POOL_SIZE):
            media_fetcher = MediaFetcher(self)
            self.media_fetchers.append(media_fetcher)
            media_fetcher_task = event_loop.create_task(media_fetcher.run())
            self.sub_tasks.append(media_fetcher_task)
        # Start the submission sender
        self.sender = Sender(self)
        task_sender = event_loop.create_task(self.sender.run())
        self.sub_tasks.append(task_sender)

    def stop_tasks(self) -> None:
        self.running = False
        if self.sub_id_gatherer:
            self.sub_id_gatherer.stop()
        for data_fetcher in self.data_fetchers:
            data_fetcher.stop()
        for media_fetcher in self.media_fetchers:
            media_fetcher.stop()
        event_loop = asyncio.get_event_loop()
        for task in self.sub_tasks[:]:
            event_loop.run_until_complete(task)
            self.sub_tasks.remove(task)
        self.data_fetchers.clear()
        self.media_fetchers.clear()

    async def run(self) -> None:
        """
        This method is launched as a task, it reads the browse endpoint for new submissions, and checks if they
        match existing subscriptions
        """
        # TODO: remove this
        self.running = True
        while self.running:
            try:
                with time_taken_listing_api.time():
                    new_results = await self._get_new_results()
            except Exception as e:
                logger.error("Failed to get new results", exc_info=e)
                continue
            count = 0
            gauge_backlog.set(len(new_results))
            with time_taken_updating_heartbeat.time():
                heartbeat.update_heartbeat(heartbeat_app_name)
            # Check for subscription updates
            for result in new_results:
                count += 1
                # If we've been told to stop, stop
                if not self.running:
                    break
                # Try and get the full data
                subs_processed.inc()
                latest_sub_processed.set_to_current_time()
                try:
                    with time_taken_submission_api.time():
                        full_result = await self.api.get_full_submission(result.submission_id)
                    logger.debug("Got full data for submission %s", result.submission_id)
                except PageNotFound:
                    logger.warning(
                        "Submission %s, disappeared before I could check it.",
                        result.submission_id,
                    )
                    subs_not_found.inc()
                    subs_failed.inc()
                    continue
                except CloudflareError:
                    logger.warning(
                        "Submission %s, returned a cloudflare error",
                        result.submission_id,
                    )
                    subs_cloudflare.inc()
                    subs_failed.inc()
                    continue
                except Exception as e:
                    logger.error("Failed to get submission %s", result.submission_id, exc_info=e)
                    subs_other_failed.inc()
                    subs_failed.inc()
                    continue
                # Log the posting date of the latest checked submission
                latest_sub_posted_at.set(full_result.posted_at.timestamp())
                # Copy subscriptions, to avoid "changed size during iteration" issues
                subscriptions = self.subscriptions.copy()
                # Check which subscriptions match
                with time_taken_checking_matches.time():
                    matching_subscriptions = []
                    for subscription in subscriptions:
                        blocklist = self.blocklists.get(subscription.destination, set())
                        blocklist_query = AndQuery([NotQuery(self.get_blocklist_query(block)) for block in blocklist])
                        if subscription.matches_result(full_result, blocklist_query):
                            matching_subscriptions.append(subscription)
                logger.debug(
                    "Submission %s matches %s subscriptions",
                    result.submission_id,
                    len(matching_subscriptions),
                )
                if matching_subscriptions:
                    sub_matches.inc()
                    sub_total_matches.inc(len(matching_subscriptions))
                    with time_taken_sending_messages.time():
                        sendable = SendableFASubmission(full_result)
                        uploaded = await sendable.upload(self.client)
                        await self._send_updates(matching_subscriptions, sendable, uploaded)
                # Update latest ids with the submission we just checked, and save config
                with time_taken_saving_config.time():
                    self.update_latest_id(sendable.submission_id)
                # Lower the backlog remaining count
                gauge_backlog.dec(1)
                # If we've done ten, update heartbeat
                if count % self.UPDATE_PER_HEARTBEAT == 0:
                    with time_taken_updating_heartbeat.time():
                        heartbeat.update_heartbeat(heartbeat_app_name)
                    logger.debug("Heartbeat")
            # Wait
            with time_taken_waiting.time():
                await self._wait_while_running(self.BACK_OFF)
        logger.info("Subscription watcher shutting down")

    def stop(self) -> None:
        logger.info("Stopping subscription watcher")
        self.running = False

    def update_latest_id(self, sub_id: SubmissionID) -> None:
        self.latest_ids.append(sub_id.submission_id)
        self.save_to_json()

    def get_blocklist_query(self, blocklist_str: str) -> Query:
        if blocklist_str not in self.blocklist_query_cache:
            self.blocklist_query_cache[blocklist_str] = parse_query(blocklist_str)
        return self.blocklist_query_cache[blocklist_str]

    def add_to_blocklist(self, destination: int, tag: str) -> None:
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
        for subscription in self.subscriptions.copy():
            if subscription.destination == old_chat_id:
                # Remove and re-add subscription, as chat id will change the hash
                self.subscriptions.remove(subscription)
                subscription.destination = new_chat_id
                self.subscriptions.add(subscription)
        # Remove old blocklist
        if old_chat_id in self.blocklists:
            del self.blocklists[old_chat_id]
        # Save
        self.save_to_json()

    def save_to_json(self) -> None:
        logger.debug("Saving subscription data in new format")
        destination_dict: Dict[str, Dict[str, List]] = collections.defaultdict(
            lambda: {"subscriptions": [], "blocks": []}
        )
        for subscription in self.subscriptions.copy():
            destination_dict[str(subscription.destination)]["subscriptions"].append(subscription.to_json())
        for dest, block_queries in self.blocklists.items():
            for block in block_queries:
                destination_dict[str(dest)]["blocks"].append({"query": block})
        data = {"latest_ids": list(self.latest_ids), "destinations": destination_dict}
        with open(self.FILENAME_TEMP, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(self.FILENAME_TEMP, self.FILENAME)

    @classmethod
    def load_from_json(
        cls,
        api: FAExportAPI,
        client: TelegramClient,
        submission_cache: SubmissionCache,
    ) -> "SubscriptionWatcher":
        logger.debug("Loading subscription config from file")
        try:
            with open(cls.FILENAME, "r") as f:
                raw_data = f.read()
                if not raw_data:
                    raise FileNotFoundError
                data = json.loads(raw_data)
        except FileNotFoundError:
            logger.info("No subscription config exists, creating a blank one")
            return cls(api, client, submission_cache)
        if "destinations" not in data:
            return cls.load_from_json_old_format(data, api, client, submission_cache)
        return cls.load_from_json_new_format(data, api, client, submission_cache)

    @classmethod
    def load_from_json_old_format(
        cls,
        data: Dict,
        api: FAExportAPI,
        client: TelegramClient,
        submission_cache: SubmissionCache,
    ) -> "SubscriptionWatcher":
        logger.debug("Loading subscription config from file in old format")
        new_watcher = cls(api, client, submission_cache)
        for old_id in data["latest_ids"]:
            new_watcher.latest_ids.append(old_id)
        new_watcher.subscriptions = set(Subscription.from_json_old_format(x) for x in data["subscriptions"])
        new_watcher.blocklists = {int(k): set(v) for k, v in data["blacklists"].items()}
        return new_watcher

    @classmethod
    def load_from_json_new_format(
        cls,
        data: Dict,
        api: FAExportAPI,
        client: TelegramClient,
        submission_cache: SubmissionCache,
    ) -> "SubscriptionWatcher":
        logger.debug("Loading subscription config from file in new format")
        new_watcher = cls(api, client, submission_cache)
        for old_id in data["latest_ids"]:
            new_watcher.latest_ids.append(old_id)
        subscriptions = set()
        for dest, value in data["destinations"].items():
            dest_id = int(dest)
            for subscription in value["subscriptions"]:
                subscriptions.add(Subscription.from_json_new_format(subscription, dest_id))
            if value["blocks"]:
                new_watcher.blocklists[dest_id] = set(block["query"] for block in value["blocks"])
        logger.debug(f"Loaded {len(subscriptions)} subscriptions")
        new_watcher.subscriptions = subscriptions
        return new_watcher
