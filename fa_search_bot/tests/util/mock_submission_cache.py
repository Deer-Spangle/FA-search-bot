from typing import Optional

from fa_search_bot.sites.sent_submission import SentSubmission
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.submission_cache import SubmissionCache


class MockSubmissionCache(SubmissionCache):
    def __init__(self):
        super().__init__(None)

    def save_cache(self, sent_submission: Optional[SentSubmission]) -> None:
        return None

    def load_cache(self, sub_id: SubmissionID, *, allow_inline: bool = False) -> Optional[SentSubmission]:
        return None
