from __future__ import annotations

import dataclasses
from asyncio import Lock
from typing import Optional, Dict, Union

from telethon.tl.types import TypeInputPeer

from fa_search_bot.sites.furaffinity.fa_submission import FASubmissionFull
from fa_search_bot.sites.sendable import UploadedMedia
from fa_search_bot.sites.sent_submission import SentSubmission
from fa_search_bot.sites.submission_id import SubmissionID


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
        self._lock = Lock()

    async def add_sub_id(self, sub_id: SubmissionID) -> None:
        async with self._lock:
            state = SubmissionCheckState(sub_id)
            self.submission_state[sub_id] = state

    async def set_fetched(self, sub_id: SubmissionID, full_data: FASubmissionFull) -> None:
        async with self._lock:
            if sub_id not in self.submission_state:
                return
            self.submission_state[sub_id].full_data = full_data

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
