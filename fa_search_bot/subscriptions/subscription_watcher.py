from __future__ import annotations

import asyncio
import collections
import dataclasses
import datetime
import json
import logging
import os
from asyncio import Lock, Queue, Task, QueueEmpty
from typing import TYPE_CHECKING

import heartbeat
from prometheus_client import Gauge, Summary
from prometheus_client.metrics import Counter
from telethon.errors import InputUserDeactivatedError, UserIsBlockedError, ChannelPrivateError, PeerIdInvalidError

from fa_search_bot.query_parser import AndQuery, NotQuery, parse_query
from fa_search_bot.sites.furaffinity.fa_export_api import CloudflareError, PageNotFound
from fa_search_bot.sites.furaffinity.sendable import SendableFASubmission
from fa_search_bot.sites.furaffinity.fa_submission import FASubmission
from fa_search_bot.sites.sendable import UploadedMedia
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.subscriptions.subscription import Subscription

if TYPE_CHECKING:
    from typing import Deque, Dict, List, Optional, Sequence, Set

    from telethon import TelegramClient
    from telethon.tl.types import TypeInputPeer

    from fa_search_bot.query_parser import Query
    from fa_search_bot.sites.furaffinity.fa_export_api import FAExportAPI
    from fa_search_bot.sites.furaffinity.fa_submission import FASubmissionFull
    from fa_search_bot.sites.sent_submission import SentSubmission
    from fa_search_bot.submission_cache import SubmissionCache, CacheEntry

heartbeat.heartbeat_app_url = "https://heartbeat.spangle.org.uk/"
heartbeat_app_name = "FASearchBot_sub_thread"

logger = logging.getLogger(__name__)
subs_processed = Counter(
    "fasearchbot_fasubwatcher_submissions_total",
    "Total number of submissions processed by the subscription watcher",
)
subs_failed = Counter(
    "fasearchbot_fasubwatcher_submissions_failed_total",
    "Number of submissions for which the sub watcher failed to get data, for any reason",
)
subs_not_found = Counter(
    "fasearchbot_fasubwatcher_not_found_total",
    "Number of submissions which disappeared before processing",
)
subs_cloudflare = Counter(
    "fasearchbot_fasubwatcher_cloudflare_errors_total",
    "Number of submissions which returned cloudflare errors",
)
subs_other_failed = Counter(
    "fasearchbot_fasubwatcher_failed_total",
    "Number of submissions for which the sub watcher failed to get data, for reasons other than 404 or cloudflare",
)
sub_matches = Counter(
    "fasearchbot_fasubwatcher_subs_which_match_total",
    "Number of submissions which match at least one subscription",
)
sub_total_matches = Counter(
    "fasearchbot_fasubwatcher_sub_matches_total",
    "Total number of subscriptions matches",
)
sub_updates = Counter("fasearchbot_fasubwatcher_updates_sent_total", "Number of subscription updates sent")
sub_blocked = Counter(
    "fasearchbot_fasubwatcher_dest_blocked_total",
    "Number of times a destination has turned out to have blocked or deleted the bot without pausing subs first",
)
sub_update_send_failures = Counter(
    "fasearchbot_fasubwatcher_updates_failed_total",
    "Number of subscription updates which failed for unknown reason",
)
latest_sub_processed = Gauge(
    "fasearchbot_fasubwatcher_latest_processed_unixtime",
    "Time that the latest submission was processed",
)
latest_sub_posted_at = Gauge(
    "fasearchbot_fasubwatcher_latest_posted_at_unixtime",
    "Time that the latest processed submission was posted on FA",
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
time_taken = Summary(
    "fasearchbot_fasubwatcher_time_taken",
    "Amount of time taken (in seconds) doing various tasks of the subscription watcher",
    labelnames=["task"],
)
time_taken_listing_api = time_taken.labels(task="listing submissions to check")
time_taken_submission_api = time_taken.labels(task="fetching submission data")
time_taken_sending_messages = time_taken.labels(task="sending messages to subscriptions")
time_taken_updating_heartbeat = time_taken.labels(task="updating heartbeat")
time_taken_checking_matches = time_taken.labels(task="checking whether submission matches subscriptions")
time_taken_saving_config = time_taken.labels(task="updating configuration")
time_taken_waiting = time_taken.labels(task="waiting before re-checking")


@dataclasses.dataclass
class SubmissionCheckState:
    sub_id: SubmissionID
    full_data: Optional[FASubmissionFull] = None
    matching_subscriptions: Optional[List[Subscription]] = None
    cache_entry: Optional[SentSubmission] = None
    uploaded_media: Optional[UploadedMedia] = None

    def key(self) -> int:
        return int(self.sub_id.submission_id)

    def is_ready_to_send(self) -> bool:
        return self.uploaded_media is not None or self.cache_entry is not None


class WaitPool:
    def __init__(self):
        self.submission_state: Dict[SubmissionID, SubmissionCheckState] = {}
        self._lock = Lock()

    async def add_sub_id(self, sub_id: SubmissionID) -> None:
        async with self._lock:
            state = SubmissionCheckState(sub_id)
            self.submission_state[sub_id] = state

    async def set_fetched(self, sub_id: SubmissionID, full_data: FASubmissionFull, matching_subs: List[Subscription]) -> None:
        async with self._lock:
            if sub_id not in self.submission_state:
                return
            self.submission_state[sub_id].full_data = full_data
            self.submission_state[sub_id].matching_subscriptions = matching_subs

    async def set_cached(self, sub_id: SubmissionID, cache_entry: SentSubmission) -> None:
        async with self._lock:
            if sub_id not in self.submission_state:
                return
            self.submission_state[sub_id].cache_entry = cache_entry

    async def set_uploaded(self, sub_id: SubmissionID, uploaded: UploadedMedia) -> None:
        async with self._lock:
            if sub_id not in self.submission_state:
                return
            self.submission_state[sub_id].uploaded_media = uploaded

    async def remove_state(self, sub_id: SubmissionID) -> None:
        async with self._lock:
            if sub_id not in self.submission_state:
                raise ValueError("This state cannot be removed because it is not in the wait pool")
            del self.submission_state[sub_id]

    async def next_submission_state(self) -> Optional[SubmissionCheckState]:
        async with self._lock:
            if not self.submission_state:
                return None
            submission_states = self.submission_state.values()
            return min(submission_states, key=lambda state: state.key())

    async def pop_next_ready_to_send(self) -> Optional[SubmissionCheckState]:
        async with self._lock:
            next_state = await self.next_submission_state()
            if not next_state:
                return None
            if not next_state.is_ready_to_send():
                return None
            await self.remove_state(next_state.sub_id)
            return next_state


class SubscriptionWatcher:
    PAGE_CAP = 900
    BACK_OFF = 20
    BROWSE_RETRY_BACKOFF = 20
    FETCH_CLOUDFLARE_BACKOFF = 60
    FETCH_EXCEPTION_BACKOFF = 20
    UPDATE_PER_HEARTBEAT = 10
    FILENAME = "subscriptions.json"
    FILENAME_TEMP = "subscriptions.temp.json"
    QUEUE_BACKOFF = 0.5
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
        self.sub_tasks: List[Task] = []

    async def _run_id_gatherer(self) -> None:
        while self.running:
            try:
                with time_taken_listing_api.time():
                    new_results = await self._get_new_results()
            except Exception as e:
                logger.error("Failed to get new results", exc_info=e)
                continue
            for result in new_results:
                sub_id = SubmissionID("fa", result.submission_id)
                await self.wait_pool.add_sub_id(sub_id)
                await self.fetch_data_queue.put(sub_id)

    async def _run_data_fetcher(self) -> None:
        while self.running:
            try:
                sub_id = self.fetch_data_queue.get_nowait()
            except QueueEmpty:
                await asyncio.sleep(self.QUEUE_BACKOFF)
                continue
            # Keep trying to fetch data
            while self.running:
                try:
                    with time_taken_submission_api.time():
                        full_result = await self.api.get_full_submission(sub_id.submission_id)
                    logger.debug("Got full data for submission %s", sub_id.submission_id)
                except PageNotFound:
                    logger.warning(
                        "Submission %s, disappeared before I could check it.",
                        sub_id.submission_id,
                    )
                    subs_not_found.inc()
                    subs_failed.inc()
                    await self.wait_pool.remove_state(sub_id)
                    continue
                except CloudflareError:
                    logger.warning(
                        "Submission %s, returned a cloudflare error, will retry in %s seconds",
                        sub_id.submission_id,
                        self.FETCH_CLOUDFLARE_BACKOFF
                    )
                    subs_cloudflare.inc()
                    subs_failed.inc()
                    await asyncio.sleep(self.FETCH_CLOUDFLARE_BACKOFF)
                    continue
                except Exception as e:
                    logger.error(
                        "Failed to get submission %s, will retry in %s seconds",
                        sub_id,
                        self.FETCH_EXCEPTION_BACKOFF,
                        exc_info=e
                    )
                    subs_other_failed.inc()
                    subs_failed.inc()
                    await asyncio.sleep(self.FETCH_EXCEPTION_BACKOFF)
                    continue
            # Log the posting date of the latest checked submission
            latest_sub_posted_at.set(full_result.posted_at.timestamp())  # TODO: make sure it's the latest
            # Copy subscriptions, to avoid "changed size during iteration" issues
            subscriptions = self.subscriptions.copy()
            # Check which subscriptions match
            with time_taken_checking_matches.time():
                matching_subscriptions = []
                for subscription in subscriptions:
                    blocklist = self.blocklists.get(subscription.destination, set())
                    blocklist_query = AndQuery([NotQuery(self._get_blocklist_query(block)) for block in blocklist])
                    if subscription.matches_result(full_result, blocklist_query):
                        matching_subscriptions.append(subscription)
            logger.debug(
                "Submission %s matches %s subscriptions",
                sub_id,
                len(matching_subscriptions),
            )
            if matching_subscriptions:
                sub_matches.inc()
                sub_total_matches.inc(len(matching_subscriptions))
                await self.wait_pool.set_fetched(sub_id, full_result, matching_subscriptions)
                await self.upload_queue.put(full_result)
            else:
                await self.wait_pool.remove_state(sub_id)

    async def _run_media_fetcher(self) -> None:
        while self.running:
            try:
                full_data = self.upload_queue.get_nowait()
            except QueueEmpty:
                await asyncio.sleep(self.QUEUE_BACKOFF)
                continue
            sendable = SendableFASubmission(full_data)
            sub_id = sendable.submission_id
            # Check if cache entry exists
            cache_entry = self.submission_cache.load_cache(sub_id)
            if cache_entry:
                await self.wait_pool.set_cached(sub_id, cache_entry)
                continue
            # Upload the file
            uploaded_media = await sendable.upload(self.client)
            await self.wait_pool.set_uploaded(sub_id, uploaded_media)

    async def _run_sender(self) -> None:
        sent_count = 0
        while self.running:
            next_state = await self.wait_pool.pop_next_ready_to_send()
            # TODO: handle cache entries
            await self._send_updates(
                next_state.matching_subscriptions,
                SendableFASubmission(next_state.full_data),
                next_state.uploaded_media,
            )
            sent_count += 1
            # Update latest ids with the submission we just checked, and save config
            with time_taken_saving_config.time():
                self._update_latest_ids([next_state.full_data])
            # If we've done ten, update heartbeat
            if sent_count % self.UPDATE_PER_HEARTBEAT == 0:
                with time_taken_updating_heartbeat.time():
                    heartbeat.update_heartbeat(heartbeat_app_name)
                logger.debug("Heartbeat")

    async def start_tasks(self) -> None:
        # TODO: Pull all these out into separate classes please, along with their helper methods
        if self.running or self.sub_tasks:
            raise ValueError("Already running")
        self.running = True
        event_loop = asyncio.get_event_loop()
        # Start the submission ID gatherer
        task_id_gatherer = event_loop.create_task(self._run_id_gatherer())
        self.sub_tasks.append(task_id_gatherer)
        # Start the data fetchers
        for _ in range(self.DATA_FETCHER_POOL_SIZE):
            data_fetcher_task = event_loop.create_task(self._run_data_fetcher())
            self.sub_tasks.append(data_fetcher_task)
        # Start the media fetchers
        for _ in range(self.MEDIA_FETCHER_POOL_SIZE):
            media_fetcher_task = event_loop.create_task(self._run_media_fetcher())
            self.sub_tasks.append(media_fetcher_task)
        # Start the submission sender
        task_sender = event_loop.create_task(self._run_sender())
        self.sub_tasks.append(task_sender)

    def stop_tasks(self) -> None:
        self.running = False
        event_loop = asyncio.get_event_loop()
        for task in self.sub_tasks[:]:
            event_loop.run_until_complete(task)
            self.sub_tasks.remove(task)

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
                        blocklist_query = AndQuery([NotQuery(self._get_blocklist_query(block)) for block in blocklist])
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
                    self._update_latest_ids([result])
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

    async def _wait_while_running(self, seconds: float) -> None:
        sleep_end = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        while datetime.datetime.now() < sleep_end:
            if not self.running:
                break
            await asyncio.sleep(0.1)

    async def _get_newest_submission(self) -> Optional[FASubmission]:
        while self.running:
            try:
                browse_results = await self.api.get_browse_page(1)
                return _latest_submission_in_list(browse_results)
            except CloudflareError:
                logger.warning("FA is under cloudflare protection, waiting before retry")
                await self._wait_while_running(self.BROWSE_RETRY_BACKOFF)
            except Exception as e:
                logger.warning("Failed to get browse page, attempting home page", exc_info=e)
            try:
                home_page = await self.api.get_home_page()
                return _latest_submission_in_list(home_page.all_submissions())
            except ValueError as e:
                logger.warning("Failed to get browse or home page, retrying", exc_info=e)
                await self._wait_while_running(self.BROWSE_RETRY_BACKOFF)
            except CloudflareError:
                logger.warning("FA is under cloudflare protection, waiting before retry")
                await self._wait_while_running(self.BROWSE_RETRY_BACKOFF)
        return None

    async def _get_new_results(self) -> List[FASubmission]:
        """
        Gets new results since last scan, returning them in order from oldest to newest.
        """
        if len(self.latest_ids) == 0:
            logger.info("First time checking subscriptions, getting initial submissions")
            newest_submission = await self._get_newest_submission()
            if not newest_submission:
                return []
            self._update_latest_ids([newest_submission])
            return []
        newest_submission = await self._get_newest_submission()
        if not newest_submission:
            return []
        newest_id = int(newest_submission.submission_id)
        latest_recorded_id = int(self.latest_ids[-1])
        logger.info("Newest ID on FA: %s, latest recorded ID: %s", newest_id, latest_recorded_id)
        new_results = [FASubmission(str(x)) for x in range(newest_id, latest_recorded_id, -1)]
        logger.info("New submissions: %s", len(new_results))
        # Return oldest result first
        return new_results[::-1]

    def _update_latest_ids(self, browse_results: Sequence[FASubmission]) -> None:
        for result in browse_results:
            self.latest_ids.append(result.submission_id)
        self.save_to_json()

    async def _send_updates(
            self,
            subscriptions: List["Subscription"],
            sendable: SendableFASubmission,
            uploaded_media: UploadedMedia,
    ) -> None:
        # Map which subscriptions require this submission at each destination
        destination_map = collections.defaultdict(lambda: [])
        for sub in subscriptions:
            sub.latest_update = datetime.datetime.now()
            destination_map[sub.destination].append(sub)
        # Send the submission to each location
        for dest, subs in destination_map.items():
            queries = ", ".join([f'"{sub.query_str}"' for sub in subs])
            prefix = f"Update on {queries} subscription{'' if len(subs) == 1 else 's'}:"
            logger.info("Sending submission %s to subscription", sendable.submission_id)
            sub_updates.inc()
            try:
                await self._send_subscription_update(sendable, uploaded_media, dest, prefix)
            except (UserIsBlockedError, InputUserDeactivatedError, ChannelPrivateError, PeerIdInvalidError):
                sub_blocked.inc()
                logger.info("Destination %s is blocked or deleted, pausing subscriptions", dest)
                all_subs = [sub for sub in self.subscriptions if sub.destination == dest]
                for sub in all_subs:
                    sub.paused = True
            except Exception as e:
                sub_update_send_failures.inc()
                logger.error(
                    "Failed to send submission: %s to %s",
                    sendable.submission_id,
                    dest,
                    exc_info=e,
                )

    async def _send_subscription_update(
        self,
        sendable: SendableFASubmission,
        uploaded: UploadedMedia,
        chat: TypeInputPeer,
        prefix: str,
    ) -> SentSubmission:
        cache_entry = self.submission_cache.load_cache(sendable.submission_id)
        if cache_entry:
            if await cache_entry.try_to_send(self.client, chat, prefix=prefix):
                return cache_entry
        result = await sendable.send_message(self.client, chat, prefix=prefix, uploaded_media=uploaded)
        self.submission_cache.save_cache(result)
        return result

    def _get_blocklist_query(self, blocklist_str: str) -> Query:
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


def _latest_submission_in_list(submissions: List[FASubmission]) -> Optional[FASubmission]:
    if not submissions:
        return None
    return max(submissions, key=lambda sub: int(sub.submission_id))
