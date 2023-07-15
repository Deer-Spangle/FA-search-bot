from __future__ import annotations

import asyncio
import logging
from asyncio import QueueEmpty

from prometheus_client import Counter
from prometheus_client.metrics import Gauge

from fa_search_bot.query_parser import AndQuery, NotQuery
from fa_search_bot.sites.furaffinity.fa_export_api import PageNotFound, CloudflareError
from fa_search_bot.subscriptions.runnable import Runnable
from fa_search_bot.subscriptions.utils import time_taken

logger = logging.getLogger(__name__)
time_taken_submission_api = time_taken.labels(task="fetching submission data")
time_taken_checking_matches = time_taken.labels(task="checking whether submission matches subscriptions")
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
latest_sub_posted_at = Gauge(
    "fasearchbot_fasubwatcher_latest_posted_at_unixtime",
    "Time that the latest processed submission was posted on FA",
)


class DataFetcher(Runnable):
    FETCH_CLOUDFLARE_BACKOFF = 60
    FETCH_EXCEPTION_BACKOFF = 20

    async def run(self) -> None:
        while self.running:
            try:
                sub_id = self.watcher.fetch_data_queue.get_nowait()
            except QueueEmpty:
                await asyncio.sleep(self.QUEUE_BACKOFF)
                continue
            # Keep trying to fetch data
            while self.running:
                try:
                    with time_taken_submission_api.time():
                        full_result = await self.watcher.api.get_full_submission(sub_id.submission_id)
                    logger.debug("Got full data for submission %s", sub_id.submission_id)
                except PageNotFound:
                    logger.warning(
                        "Submission %s, disappeared before I could check it.",
                        sub_id.submission_id,
                    )
                    subs_not_found.inc()
                    subs_failed.inc()
                    await self.watcher.wait_pool.remove_state(sub_id)
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
            subscriptions = self.watcher.subscriptions.copy()
            # Check which subscriptions match
            with time_taken_checking_matches.time():
                matching_subscriptions = []
                for subscription in subscriptions:
                    blocklist = self.watcher.blocklists.get(subscription.destination, set())
                    blocklist_query = AndQuery(
                        [NotQuery(self.watcher.get_blocklist_query(block)) for block in blocklist]
                    )
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
                await self.watcher.wait_pool.set_fetched(sub_id, full_result, matching_subscriptions)
                await self.watcher.upload_queue.put(full_result)
            else:
                await self.watcher.wait_pool.remove_state(sub_id)
