from __future__ import annotations

import logging
from typing import List, Optional

import heartbeat
from prometheus_client import Gauge, Counter

from fa_search_bot.sites.furaffinity.fa_export_api import CloudflareError
from fa_search_bot.sites.furaffinity.fa_submission import FASubmission
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.subscriptions.runnable import Runnable
from fa_search_bot.subscriptions.utils import time_taken, _latest_submission_in_list

logger = logging.getLogger(__name__)

heartbeat.heartbeat_app_url = "https://heartbeat.spangle.org.uk/"
heartbeat_app_name = "FASearchBot_task_SubIDGatherer"

time_taken_listing_api = time_taken.labels(task="listing submissions to check", runnable="SubIDGatherer")
time_taken_waiting = time_taken.labels(task="waiting before re-checking", runnable="SubIDGatherer")
time_taken_publishing = time_taken.labels(task="publishing results to queues", runnable="SubIDGatherer")
time_taken_updating_heartbeat = time_taken.labels(task="updating heartbeat", runnable="SubIDGatherer")
latest_id_published = Gauge(
    "fasearchbot_subidgatherer_latest_id_published_unixtime",
    "UNIX timestamp that the latest submission ID got published to queues",
)
published_ID_counter = Counter(
    "fasearchbot_subidgatherer_total_published_sub_id_count",
    "Count of how many submission IDs have been published to queues",
)


class SubIDGatherer(Runnable):
    BROWSE_RETRY_BACKOFF = 20
    NEW_ID_BACKOFF = 20
    UPDATE_PER_HEARTBEAT = 20

    async def run(self) -> None:
        published_count = 0
        self.running = True
        while self.running:
            try:
                with time_taken_listing_api.time():
                    new_results = await self._get_new_results()
            except Exception as e:
                logger.error("Failed to get new results", exc_info=e)
                continue
            for result in new_results:
                sub_id = SubmissionID("fa", result.submission_id)
                # Publish submission ID to queues for the other tasks
                with time_taken_publishing.time():
                    await self.watcher.wait_pool.add_sub_id(sub_id)
                    await self.watcher.fetch_data_queue.put(sub_id)
                # Metrics
                published_ID_counter.inc()
                latest_id_published.set_to_current_time()
                self.heartbeat(published_count)
            # Wait before checking for more
            with time_taken_waiting.time():
                await self._wait_while_running(self.NEW_ID_BACKOFF)

    async def _get_new_results(self) -> List[FASubmission]:
        """
        Gets new results since last scan, returning them in order from oldest to newest.
        """
        if len(self.watcher.latest_ids) == 0:
            logger.info("First time checking subscriptions, getting initial submissions")
            newest_submission = await self._get_newest_submission()
            if not newest_submission:
                return []
            self.watcher.update_latest_id(SubmissionID("fa", newest_submission.submission_id))
            return []
        newest_submission = await self._get_newest_submission()
        if not newest_submission:
            return []
        newest_id = int(newest_submission.submission_id)
        latest_recorded_id = int(self.watcher.latest_ids[-1])
        logger.info("Newest ID on FA: %s, latest recorded ID: %s", newest_id, latest_recorded_id)
        new_results = [FASubmission(str(x)) for x in range(newest_id, latest_recorded_id, -1)]
        logger.info("New submissions: %s", len(new_results))
        # Return oldest result first
        return new_results[::-1]

    async def _get_newest_submission(self) -> Optional[FASubmission]:
        while self.running:
            try:
                browse_results = await self.watcher.api.get_browse_page(1)
                return _latest_submission_in_list(browse_results)
            except CloudflareError:
                logger.warning("FA is under cloudflare protection, waiting before retry")
                await self._wait_while_running(self.BROWSE_RETRY_BACKOFF)
            except Exception as e:
                logger.warning("Failed to get browse page, attempting home page", exc_info=e)
            try:
                home_page = await self.watcher.api.get_home_page()
                return _latest_submission_in_list(home_page.all_submissions())
            except ValueError as e:
                logger.warning("Failed to get browse or home page, retrying", exc_info=e)
                await self._wait_while_running(self.BROWSE_RETRY_BACKOFF)
            except CloudflareError:
                logger.warning("FA is under cloudflare protection, waiting before retry")
                await self._wait_while_running(self.BROWSE_RETRY_BACKOFF)
        return None

    def heartbeat(self, published_count: int) -> None:
        if published_count % self.UPDATE_PER_HEARTBEAT == 0:
            with time_taken_updating_heartbeat.time():
                heartbeat.update_heartbeat(heartbeat_app_name)
            logger.debug("Heartbeat from SubIDGatherer")
