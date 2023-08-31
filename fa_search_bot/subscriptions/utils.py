from asyncio import Queue, QueueEmpty
from typing import List, Optional

from prometheus_client import Summary

from fa_search_bot.sites.furaffinity.fa_submission import FASubmission
from fa_search_bot.sites.submission_id import SubmissionID

time_taken = Summary(
    "fasearchbot_fasubwatcher_time_taken",
    "Amount of time taken (in seconds) doing various tasks of the subscription watcher",
    labelnames=["runnable", "task"],
)


def _latest_submission_in_list(submissions: List[FASubmission]) -> Optional[FASubmission]:
    if not submissions:
        return None
    return max(submissions, key=lambda sub: int(sub.submission_id))


class FetchQueue:
    PRIORITY_NEW_FETCH = 10
    PRIORITY_REFRESH = 5

    def __init__(self):
        self._new_queue: Queue[SubmissionID] = Queue()
        self._refresh_queue: Queue[SubmissionID] = Queue()

    def get_nowait(self) -> SubmissionID:
        try:
            return self._refresh_queue.get_nowait()
        except QueueEmpty:
            return self._new_queue.get_nowait()

    async def put_new(self, sub_id: SubmissionID) -> None:
        await self._new_queue.put(sub_id)

    async def put_refresh(self, sub_id: SubmissionID) -> None:
        await self._refresh_queue.put(sub_id)

    def qsize(self) -> int:
        return self._refresh_queue.qsize() + self._new_queue.qsize()

    def qsize_new(self) -> int:
        return self._new_queue.qsize()

    def qsize_refresh(self) -> int:
        return self._refresh_queue.qsize()
