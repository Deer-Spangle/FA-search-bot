from __future__ import annotations

import asyncio
import logging
from asyncio import QueueEmpty
from typing import Optional

from aiohttp import ClientPayloadError
from prometheus_client import Counter

from fa_search_bot.sites.furaffinity.sendable import SendableFASubmission
from fa_search_bot.sites.sendable import UploadedMedia, DownloadError, SendSettings, CaptionSettings
from fa_search_bot.subscriptions.runnable import Runnable, ShutdownError
from fa_search_bot.subscriptions.utils import time_taken, TooManyRefresh

logger = logging.getLogger(__name__)

time_taken_waiting = time_taken.labels(task="waiting for new events in queue", runnable="MediaFetcher")
time_taken_uploading = time_taken.labels(task="uploading media to telegram", runnable="MediaFetcher")
time_taken_publishing = time_taken.labels(task="publishing results to queues", runnable="MediaFetcher")
cache_results = Counter(
    "fasearchbot_mediafetcher_cache_fetch_count",
    "Count of how many times the media fetcher checked the cache for submission media",
    labelnames=["result"]
)
cache_hits = cache_results.labels(result="hit")
cache_misses = cache_results.labels(result="miss")


class MediaFetcher(Runnable):
    CONNECTION_BACKOFF = 20

    async def do_process(self) -> None:
        try:
            full_data = self.watcher.upload_queue.get_nowait()
        except QueueEmpty:
            with time_taken_waiting.time():
                await asyncio.sleep(self.QUEUE_BACKOFF)
            return
        sendable = SendableFASubmission(full_data)
        sub_id = sendable.submission_id
        logger.debug("Got %s from queue, uploading media", sub_id)
        # Check if cache entry exists
        cache_entry = self.watcher.submission_cache.load_cache(sub_id)
        if cache_entry:
            cache_hits.inc()
            logger.debug("Got cache entry for %s, setting in waitpool", sub_id)
            with time_taken_publishing.time():
                await self.watcher.wait_pool.set_cached(sub_id, cache_entry)
            return
        cache_misses.inc()
        # Upload the file
        logger.debug("Uploading submission media: %s", sub_id)
        try:
            with time_taken_uploading.time():
                uploaded_media = await self.upload_sendable(sendable)
        except DownloadError as e:
            if e.exc.status != 404:
                raise e
            uploaded_media = await self.handle_deleted(sendable)
            if not uploaded_media:
                return
        logger.debug("Upload complete for %s, publishing to wait pool", sub_id)
        with time_taken_publishing.time():
            await self.watcher.wait_pool.set_uploaded(sub_id, uploaded_media)

    async def handle_deleted(self, sendable: SendableFASubmission) -> Optional[UploadedMedia]:
        sub_id = sendable.submission_id
        logger.debug("Media for %s disappeared before it could be uploaded, throwing back to the fetch queue", sub_id)
        try:
            await self.watcher.fetch_data_queue.put_refresh(sub_id)
        except TooManyRefresh:
            logger.warning(
                "Image could not be fetched for %s after %s refreshes. Sending without media",
                sub_id,
                self.watcher.fetch_data_queue.refresh_counter.refresh_limit
            )
            return UploadedMedia(sub_id, None, SendSettings(CaptionSettings(False, True, True, True), False, False))

    async def upload_sendable(self, sendable: SendableFASubmission) -> Optional[UploadedMedia]:
        while self.running:
            try:
                return await sendable.upload(self.watcher.client)
            except ConnectionError as e:
                logger.warning(
                    "Upload failed, telegram has disconnected, trying again in %s",
                    self.CONNECTION_BACKOFF,
                    exc_info=e
                )
                await self._wait_while_running(self.CONNECTION_BACKOFF)
                continue
            except ClientPayloadError as e:
                logger.warning(
                    "Upload failed, telegram response incomplete, trying again in %s",
                    self.CONNECTION_BACKOFF,
                    exc_info=e,
                )
                await self._wait_while_running(self.CONNECTION_BACKOFF)
                continue
            except DownloadError as e:
                if e.exc.status in [502, 520, 403]:
                    logger.warning(
                        "Media download failed with %s error. Trying again in %s",
                        e.exc.status,
                        self.CONNECTION_BACKOFF,
                    )
                    await self._wait_while_running(self.CONNECTION_BACKOFF)
                    continue
                raise e
        raise ShutdownError("Media fetcher has shutdown while trying to upload media")
