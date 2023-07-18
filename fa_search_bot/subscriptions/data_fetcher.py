from __future__ import annotations

import asyncio
import logging
from asyncio import QueueEmpty
from typing import Optional

from prometheus_client import Counter, Histogram, Gauge

from fa_search_bot.query_parser import AndQuery, NotQuery
from fa_search_bot.sites.furaffinity.fa_export_api import PageNotFound, CloudflareError
from fa_search_bot.sites.furaffinity.fa_submission import FASubmissionFull
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.subscriptions.runnable import Runnable
from fa_search_bot.subscriptions.utils import time_taken

logger = logging.getLogger(__name__)

# Time usage metrics
time_taken_queue_waiting = time_taken.labels(task="waiting for new events in queue", runnable="DataFetcher")
time_taken_submission_api = time_taken.labels(task="fetching submission data", runnable="DataFetcher")
time_taken_checking_matches = time_taken.labels(
    task="checking whether submission matches subscriptions",
    runnable="DataFetcher",
)
time_taken_publishing = time_taken.labels(task="publishing results to queues", runnable="DataFetcher")
time_taken_cloudflare_backoff = time_taken.labels(task="waiting after cloudflare error", runnable="DataFetcher")
time_taken_error_backoff = time_taken.labels(task="waiting after unknown error", runnable="DataFetcher")
# Fetch attempt metrics
counter_fetch_attempts = Counter(
    "fasearchbot_datafetcher_fetch_attempt_count",
    "Number of attempts the data fetcher makes to fetch data about a submission, and the result",
    labelnames=["result"],
)
fetch_attempts_success = counter_fetch_attempts.labels(result="success")
fetch_attempts_cloudflare = counter_fetch_attempts.labels(result="cloudflare_error")
fetch_attempts_not_found = counter_fetch_attempts.labels(result="not_found")
fetch_attempts_error = counter_fetch_attempts.labels(result="error")
histogram_fetch_attempts = Histogram(
    "fasearchbot_datafetcher_fetch_attempts_required",
    "Number of fetch attempts required for each submission ID",
    buckets=[1, 2, 3, 5, 10, float("inf")]
)
# Subs processed metrics
counter_subs_processed = Counter(
    "fasearchbot_datafetcher_ids_processed_count",
    "Number of submission IDs that have been processed by the data fetchers",
    labelnames=["result"]
)
latest_fetched = Gauge(
    "fasearchbot_datafetcher_latest_id_fetched_unixtime",
    "UNIX timestamp of when the latest submission was fetched from the API",
)
counter_subs_found = counter_subs_processed.labels(result="fetched")
counter_subs_missed = counter_subs_processed.labels(result="not_found")
# Subscription results metrics
sub_matches = Counter(
    "fasearchbot_datafetcher_subs_which_match_total",
    "Number of submissions which match at least one subscription",
)
sub_total_matches = Counter(
    "fasearchbot_datafetcher_sub_matches_total",
    "Total number of subscriptions matches",
)


class DataFetcher(Runnable):
    FETCH_CLOUDFLARE_BACKOFF = 60
    FETCH_EXCEPTION_BACKOFF = 20

    async def do_process(self) -> None:
        try:
            sub_id = self.watcher.fetch_data_queue.get_nowait()
        except QueueEmpty:
            with time_taken_queue_waiting.time():
                await asyncio.sleep(self.QUEUE_BACKOFF)
            return
        # Fetch data
        logger.debug("Got %s from queue, fetching data", sub_id)
        full_result = await self.fetch_data(sub_id)
        if full_result is None:
            counter_subs_missed.inc()
            return
        counter_subs_found.inc()
        # Log the posting date of the latest checked submission
        self.watcher.update_latest_observed(full_result.posted_at)
        # See which subscriptions match the submission
        with time_taken_checking_matches.time():
            matching_subscriptions = await self.check_subscriptions(full_result)
        logger.debug("Submission %s matches %s subscriptions", sub_id, len(matching_subscriptions))
        # Publish results
        if matching_subscriptions:
            sub_matches.inc()
            sub_total_matches.inc(len(matching_subscriptions))
            with time_taken_publishing.time():
                await self.watcher.wait_pool.set_fetched(sub_id, full_result, matching_subscriptions)
                await self.watcher.upload_queue.put(full_result)
        else:
            with time_taken_publishing.time():
                await self.watcher.wait_pool.remove_state(sub_id)

    async def fetch_data(self, sub_id: SubmissionID) -> Optional[FASubmissionFull]:
        # Keep trying to fetch data, unless it is gone
        attempts = 0
        while self.running:
            try:
                with time_taken_submission_api.time():
                    attempts += 1
                    full_result = await self.watcher.api.get_full_submission(sub_id.submission_id)
                logger.debug("Got full data for submission %s", sub_id.submission_id)
                fetch_attempts_success.inc()
                histogram_fetch_attempts.observe(attempts)
                return full_result
            except PageNotFound:
                logger.warning("Submission %s, disappeared before I could check it.", sub_id)
                fetch_attempts_not_found.inc()
                with time_taken_publishing.time():
                    await self.watcher.wait_pool.remove_state(sub_id)
                histogram_fetch_attempts.observe(attempts)
                return None
            except CloudflareError:
                logger.warning(
                    "Submission %s, returned a cloudflare error, will retry in %s seconds",
                    sub_id,
                    self.FETCH_CLOUDFLARE_BACKOFF
                )
                fetch_attempts_cloudflare.inc()
                with time_taken_cloudflare_backoff.time():
                    await asyncio.sleep(self.FETCH_CLOUDFLARE_BACKOFF)
                continue
            except Exception as e:
                logger.error(
                    "Failed to get submission %s, will retry in %s seconds",
                    sub_id,
                    self.FETCH_EXCEPTION_BACKOFF,
                    exc_info=e
                )
                fetch_attempts_error.inc()
                with time_taken_error_backoff.time():
                    await asyncio.sleep(self.FETCH_EXCEPTION_BACKOFF)
                continue

    async def check_subscriptions(self, full_result):
        # Copy subscriptions, to avoid "changed size during iteration" issues
        subscriptions = self.watcher.subscriptions.copy()
        # Check which subscriptions match
        matching_subscriptions = []
        for subscription in subscriptions:
            blocklist = self.watcher.blocklists.get(subscription.destination, set())
            blocklist_query = AndQuery(
                [NotQuery(self.watcher.get_blocklist_query(block)) for block in blocklist]
            )
            if subscription.matches_result(full_result, blocklist_query):
                matching_subscriptions.append(subscription)
        return matching_subscriptions
