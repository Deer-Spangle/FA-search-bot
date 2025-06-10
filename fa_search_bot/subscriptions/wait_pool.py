from __future__ import annotations

import dataclasses
from asyncio import Lock, Queue
from typing import Optional, Dict, Union

from telethon.tl.types import TypeInputPeer

from fa_search_bot.sites.furaffinity.fa_submission import FASubmissionFull
from fa_search_bot.sites.sendable import UploadedMedia
from fa_search_bot.sites.sent_submission import SentSubmission
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.subscriptions.fetch_queue import FetchQueue


@dataclasses.dataclass
class SubmissionCheckState:
    sub_id: SubmissionID
    full_data: Optional[FASubmissionFull] = None
    cache_entry: Optional[SentSubmission] = None
    uploaded_media: Optional[UploadedMedia] = None
    sent_to: list[Union[int, TypeInputPeer]] = dataclasses.field(default_factory=list)

    def key(self) -> int:
        return int(self.sub_id.submission_id)

    def is_ready_to_send(self) -> bool:
        return self.uploaded_media is not None or self.cache_entry is not None


class WaitPool:
    """
    WaitPool governs the overall progress of the subscription watcher. New IDs are added here, and then populated by the
    data fetchers and media watchers.
    The sender is watching for the next item in the pool which is ready to send
    """
    def __init__(self):
        self.submission_state: Dict[SubmissionID, SubmissionCheckState] = {}
        self.fetch_data_queue: FetchQueue = FetchQueue()
        self.upload_queue: Queue[FASubmissionFull] = Queue(500)  # Size limit to prevent data being too stale by the time it comes to upload, especially if catching up on backlog
        self._lock = Lock()

    async def add_sub_id(self, sub_id: SubmissionID) -> None:
        async with self._lock:
            state = SubmissionCheckState(sub_id)
            self.submission_state[sub_id] = state
            await self.fetch_data_queue.put_new(sub_id)

    async def get_next_for_data_fetch(self) -> SubmissionID:
        return self.fetch_data_queue.get_nowait()

    async def set_fetched_data(self, sub_id: SubmissionID, full_data: FASubmissionFull) -> None:
        async with self._lock:
            if sub_id not in self.submission_state:
                return
            self.submission_state[sub_id].full_data = full_data
            await self.upload_queue.put(full_data)

    async def revert_data_fetch(self, sub_id: SubmissionID) -> None:
        # This reverts a submission back to before any data was fetched about it, and re-queues it for data fetch
        async with self._lock:
            if sub_id not in self.submission_state:
                self.submission_state[sub_id] = SubmissionCheckState(sub_id)
            self.submission_state[sub_id].full_data = None
            self.submission_state[sub_id].cache_entry = None
            self.submission_state[sub_id].uploaded_media = None
            await self.fetch_data_queue.put_refresh(sub_id)

    async def get_next_for_media_upload(self) -> FASubmissionFull:
        return self.upload_queue.get_nowait()

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

    async def pop_next_ready_to_send(self) -> Optional[SubmissionCheckState]:
        async with self._lock:
            submission_states = self.submission_state.values()
            if not submission_states:
                return None
            next_state = min(submission_states, key=lambda state: state.key())
            if not next_state.is_ready_to_send():
                return None
            del self.submission_state[next_state.sub_id]
            return next_state

    async def return_populated_state(self, state: SubmissionCheckState) -> None:
        async with self._lock:
            self.submission_state[state.sub_id] = state

    def size(self) -> int:
        return len(self.submission_state)

    def qsize_fetch_new(self) -> int:
        return self.fetch_data_queue.qsize_new()

    def qsize_fetch_refresh(self) -> int:
        return self.fetch_data_queue.qsize_refresh()

    def qsize_upload(self) -> int:
        return self.upload_queue.qsize()
