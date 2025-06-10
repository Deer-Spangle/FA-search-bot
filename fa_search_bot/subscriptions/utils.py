from typing import List, Optional

from prometheus_client import Summary

from fa_search_bot.sites.furaffinity.fa_submission import FASubmission

time_taken = Summary(
    "fasearchbot_fasubwatcher_time_taken",
    "Amount of time taken (in seconds) doing various tasks of the subscription watcher",
    labelnames=["runnable", "task"],
)


def _latest_submission_in_list(submissions: List[FASubmission]) -> Optional[FASubmission]:
    if not submissions:
        return None
    return max(submissions, key=lambda sub: int(sub.submission_id))


