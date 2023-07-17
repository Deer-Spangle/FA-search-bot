from __future__ import annotations

import asyncio
from asyncio import QueueEmpty

from prometheus_client import Counter

from fa_search_bot.sites.furaffinity.sendable import SendableFASubmission
from fa_search_bot.subscriptions.runnable import Runnable
from fa_search_bot.subscriptions.utils import time_taken


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

    async def do_process(self) -> None:
        try:
            full_data = self.watcher.upload_queue.get_nowait()
        except QueueEmpty:
            with time_taken_waiting.time():
                await asyncio.sleep(self.QUEUE_BACKOFF)
            return
        sendable = SendableFASubmission(full_data)
        sub_id = sendable.submission_id
        # Check if cache entry exists
        cache_entry = self.watcher.submission_cache.load_cache(sub_id)
        if cache_entry:
            cache_hits.inc()
            with time_taken_publishing.time():
                await self.watcher.wait_pool.set_cached(sub_id, cache_entry)
            return
        cache_misses.inc()
        # Upload the file
        with time_taken_uploading.time():
            uploaded_media = await sendable.upload(self.watcher.client)
        with time_taken_publishing.time():
            await self.watcher.wait_pool.set_uploaded(sub_id, uploaded_media)
