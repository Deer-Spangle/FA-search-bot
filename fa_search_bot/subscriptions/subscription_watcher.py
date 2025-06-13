from __future__ import annotations

import asyncio
import collections
import datetime
import json
import logging
import os
from asyncio import Task
from typing import TYPE_CHECKING

from prometheus_client import Gauge

from fa_search_bot.config import SubscriptionWatcherConfig
from fa_search_bot.subscriptions.runnable import ShutdownError
from fa_search_bot.subscriptions.query_parser import parse_query, Query, AndQuery, NotQuery
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.subscriptions.data_fetcher import DataFetcher
from fa_search_bot.subscriptions.media_fetcher import MediaFetcher
from fa_search_bot.subscriptions.sender import Sender
from fa_search_bot.subscriptions.sub_id_gatherer import SubIDGatherer
from fa_search_bot.subscriptions.subscription import Subscription
from fa_search_bot.subscriptions.wait_pool import WaitPool

if TYPE_CHECKING:
    from typing import Deque, Dict, List, Optional, Set

    from telethon import TelegramClient

    from fa_search_bot.sites.furaffinity.fa_export_api import FAExportAPI
    from fa_search_bot.sites.furaffinity.fa_submission import FASubmissionFull
    from fa_search_bot.submission_cache import SubmissionCache

logger = logging.getLogger(__name__)
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
gauge_wait_pool_size = Gauge(
    "fasearchbot_fasubwatcher_wait_pool_size",
    "Total number of submissions in the wait pool",
)
gauge_fetch_queue_size = Gauge(
    "fasearchbot_fasubwatcher_fetch_data_queue_size",
    "Total number of submission IDs in the fetch data queue",
    labelnames=["sub_queue"]
)
gauge_fetch_queue_new_size = gauge_fetch_queue_size.labels(sub_queue="new")
gauge_fetch_queue_refresh_size = gauge_fetch_queue_size.labels(sub_queue="refresh")
gauge_upload_queue_size = Gauge(
    "fasearchbot_fasubwatcher_upload_queue_size",
    "Total number of submissions in the upload queue",
)
gauge_running_data_fetcher_count = Gauge(
    "fasearchbot_fasubwatcher_running_data_fetcher_count",
    "Number of running data fetcher tasks",
)
gauge_expected_data_fetcher_count = Gauge(
    "fasearchbot_fasubwatcher_expected_data_fetcher_count",
    "Number of expected data fetcher tasks which should be running",
)
gauge_running_media_fetcher_count = Gauge(
    "fasearchbot_fasubwatcher_running_media_fetcher_count",
    "Number of running media fetcher tasks",
)
gauge_expected_media_fetcher_count = Gauge(
    "fasearchbot_fasubwatcher_expected_media_fetcher_count",
    "Number of expected media fetcher tasks which should be running",
)
gauge_running_task_count = Gauge(
    "fasearchbot_fasubwatcher_running_task_count",
    "Number of running tasks",
)
gauge_expected_task_count = Gauge(
    "fasearchbot_fasubwatcher_expected_task_count",
    "Total number of tasks which are expected to be running",
)
latest_sub_posted_at = Gauge(
    "fasearchbot_fasubwatcher_latest_posted_at_unixtime",
    "Time that the latest posted submission was posted on FA",
)


class SubscriptionWatcher:
    BACK_OFF = 20
    FILENAME = "subscriptions.json"
    FILENAME_TEMP = "subscriptions.temp.json"

    def __init__(
            self,
            config: SubscriptionWatcherConfig,
            api: FAExportAPI,
            client: TelegramClient,
            submission_cache: SubmissionCache,
    ) -> None:
        self.config = config
        self.api = api
        self.client = client
        self.submission_cache = submission_cache

        # Initialise stored data structures
        self.latest_ids: Deque[str] = collections.deque(maxlen=15)
        self.subscriptions: Set[Subscription] = set()
        self.blocklists: Dict[int, Set[str]] = dict()
        self.blocklist_query_cache: Dict[str, Query] = dict()

        # Initialise sharing data structures
        self.wait_pool = WaitPool()

        # Initialise runners and tasks
        self.sub_id_gatherer: Optional[SubIDGatherer] = None
        self.data_fetchers: List[DataFetcher] = []
        self.media_fetchers: List[MediaFetcher] = []
        self.sender: Optional[Sender] = None
        self.sub_tasks: List[Task] = []

        # Initialise gauges and prometheus metrics
        self.latest_observed_submission: Optional[datetime.datetime] = None
        gauge_sub.set_function(lambda: len(self.subscriptions))
        gauge_subs_active.set_function(lambda: len([s for s in self.subscriptions if not s.paused]))
        gauge_sub_destinations.set_function(lambda: len(set(s.destination for s in self.subscriptions)))
        gauge_sub_active_destinations.set_function(
            lambda: len(set(s.destination for s in self.subscriptions if not s.paused))
        )
        gauge_sub_blocks.set_function(lambda: sum(len(blocks) for blocks in self.blocklists.values()))
        gauge_wait_pool_size.set_function(lambda: self.wait_pool.size())
        gauge_fetch_queue_new_size.set_function(lambda: self.wait_pool.qsize_fetch_new())
        gauge_fetch_queue_refresh_size.set_function(lambda: self.wait_pool.qsize_fetch_refresh())
        gauge_upload_queue_size.set_function(lambda: self.wait_pool.qsize_upload())
        gauge_running_data_fetcher_count.set_function(lambda: len([f for f in self.data_fetchers if f.running]))
        gauge_expected_data_fetcher_count.set(self.config.num_data_fetchers)
        gauge_running_media_fetcher_count.set_function(lambda: len([f for f in self.media_fetchers if f.running]))
        gauge_expected_media_fetcher_count.set(self.config.num_media_uploaders)
        gauge_running_task_count.set_function(lambda: len([t for t in self.sub_tasks if not t.done()]))
        gauge_expected_task_count.set(2+self.config.num_data_fetchers+self.config.num_media_uploaders)

    def start_tasks(self) -> None:
        if self.sub_tasks:
            raise RuntimeError("Already running")
        event_loop = asyncio.get_event_loop()
        # Start the submission ID gatherer
        self.sub_id_gatherer = SubIDGatherer(self)
        sub_id_gatherer_task = event_loop.create_task(self.sub_id_gatherer.run())
        self.sub_tasks.append(sub_id_gatherer_task)
        # Start the data fetchers
        for _ in range(self.config.num_data_fetchers):
            data_fetcher = DataFetcher(self)
            self.data_fetchers.append(data_fetcher)
            data_fetcher_task = event_loop.create_task(data_fetcher.run())
            self.sub_tasks.append(data_fetcher_task)
        # Start the media fetchers
        for _ in range(self.config.num_media_uploaders):
            media_fetcher = MediaFetcher(self)
            self.media_fetchers.append(media_fetcher)
            media_fetcher_task = event_loop.create_task(media_fetcher.run())
            self.sub_tasks.append(media_fetcher_task)
        # Start the submission sender
        self.sender = Sender(self)
        task_sender = event_loop.create_task(self.sender.run())
        self.sub_tasks.append(task_sender)

    def stop_tasks(self) -> None:
        # Ask runnables to stop
        logger.info("Shutting down subscription watcher")
        if self.sub_id_gatherer:
            logger.debug("Stopping Sub ID gatherer")
            self.sub_id_gatherer.stop()
        for data_fetcher in self.data_fetchers:
            logger.debug("Stopping data fetcher")
            data_fetcher.stop()
        for media_fetcher in self.media_fetchers:
            logger.debug("Stopping media fetcher")
            media_fetcher.stop()
        if self.sender:
            logger.debug("Stopping sender")
            self.sender.stop()
        # Shut down running tasks
        event_loop = asyncio.get_event_loop()
        for task in self.sub_tasks[:]:
            if task.done():
                logger.debug("Task already shut down")
                continue
            logger.debug("Waiting for task shutdown")
            try:
                event_loop.run_until_complete(task)
            except ShutdownError:
                pass
            self.sub_tasks.remove(task)
        # Clean up fetchers
        self.data_fetchers.clear()
        self.media_fetchers.clear()
        logger.info("Subscription watcher shutdown complete")

    def update_latest_observed(self, post_datetime: datetime.datetime) -> None:
        if self.latest_observed_submission is None or post_datetime > self.latest_observed_submission:
            self.latest_observed_submission = post_datetime
            latest_sub_posted_at.set(post_datetime.timestamp())

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

    def check_subscriptions(self, full_result: FASubmissionFull) -> List[Subscription]:
        # Copy subscriptions, to avoid "changed size during iteration" issues
        subscriptions = self.subscriptions.copy()
        # Check which subscriptions match
        matching_subscriptions = []
        for subscription in subscriptions:
            blocklist = self.blocklists.get(subscription.destination, set())
            blocklist_query = AndQuery(
                [NotQuery(self.get_blocklist_query(block)) for block in blocklist]
            )
            if subscription.matches_result(full_result, blocklist_query):
                matching_subscriptions.append(subscription)
        return matching_subscriptions

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
        config: SubscriptionWatcherConfig,
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
            return cls(config, api, client, submission_cache)
        return cls.load_from_json_new_format(data, config, api, client, submission_cache)

    @classmethod
    def load_from_json_new_format(
        cls,
        data: Dict,
        config: SubscriptionWatcherConfig,
        api: FAExportAPI,
        client: TelegramClient,
        submission_cache: SubmissionCache,
    ) -> "SubscriptionWatcher":
        logger.debug("Loading subscription config from file in new format")
        new_watcher = cls(config, api, client, submission_cache)
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
