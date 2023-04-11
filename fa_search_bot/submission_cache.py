import dataclasses
import datetime
from typing import Optional

from fa_search_bot.database import Database, DBCacheEntry
from fa_search_bot.sites.sent_submission import SentSubmission
from fa_search_bot.sites.submission_id import SubmissionID


def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


@dataclasses.dataclass
class CacheEntry:
    sent_submission: SentSubmission
    cache_date: datetime.datetime


class SubmissionCache:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save_cache(self, sent_submission: Optional[SentSubmission]) -> None:
        if sent_submission is None:
            return
        cache_entry = DBCacheEntry(
            sent_submission.sub_id.site_code,
            str(sent_submission.sub_id.submission_id),
            sent_submission.is_photo,
            sent_submission.media_id,
            sent_submission.access_hash,
            sent_submission.file_url,
            sent_submission.caption,
            now(),
            sent_submission.full_image,
        )
        self.db.save_cache_entry(cache_entry)

    def load_cache(self, sub_id: SubmissionID, *, allow_inline: bool = False) -> Optional[SentSubmission]:
        entry = self.db.fetch_cache_entry(sub_id.site_code, str(sub_id.submission_id))
        if entry is None:
            return None
        # Unless this is for inline use, only return full image results
        if not allow_inline and not entry.full_image:
            return None
        return SentSubmission(
            SubmissionID(entry.site_code, entry.submission_id),
            entry.is_photo,
            entry.media_id,
            entry.access_hash,
            entry.file_url,
            entry.caption,
        )
