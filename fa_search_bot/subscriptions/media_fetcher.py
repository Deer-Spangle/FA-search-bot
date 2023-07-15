from __future__ import annotations

import asyncio
from asyncio import QueueEmpty

from fa_search_bot.sites.furaffinity.sendable import SendableFASubmission
from fa_search_bot.subscriptions.runnable import Runnable


class MediaFetcher(Runnable):

    async def run(self) -> None:
        while self.running:
            try:
                full_data = self.watcher.upload_queue.get_nowait()
            except QueueEmpty:
                await asyncio.sleep(self.QUEUE_BACKOFF)
                continue
            sendable = SendableFASubmission(full_data)
            sub_id = sendable.submission_id
            # Check if cache entry exists
            cache_entry = self.watcher.submission_cache.load_cache(sub_id)
            if cache_entry:
                await self.watcher.wait_pool.set_cached(sub_id, cache_entry)
                continue
            # Upload the file
            uploaded_media = await sendable.upload(self.watcher.client)
            await self.watcher.wait_pool.set_uploaded(sub_id, uploaded_media)
