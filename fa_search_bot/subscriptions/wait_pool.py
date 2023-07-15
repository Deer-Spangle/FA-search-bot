from __future__ import annotations

import dataclasses
from asyncio import Lock
from typing import Optional, List, Dict

from fa_search_bot.sites.furaffinity.fa_submission import FASubmissionFull
from fa_search_bot.sites.sendable import UploadedMedia
from fa_search_bot.sites.sent_submission import SentSubmission
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.subscriptions.subscription import Subscription


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
