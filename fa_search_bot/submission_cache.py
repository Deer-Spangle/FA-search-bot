import dataclasses
import datetime
from typing import Optional

from fa_search_bot.database import Database, DBCacheEntry
from fa_search_bot.sites.site_handler import SentSubmission, SubmissionID


def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


@dataclasses.dataclass
class CacheEntry:
    sent_submission: SentSubmission
    cache_date: datetime.datetime


class SubmissionCache:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save_cache(self, sent_submission: SentSubmission) -> None:
        cache_entry = DBCacheEntry(
            sent_submission.sub_id.site_code,
            str(sent_submission.sub_id.submission_id),
            sent_submission.is_photo,
            sent_submission.media_id,
            sent_submission.access_hash,
            sent_submission.file_url,
            sent_submission.caption,
            now(),
        )
        self.db.save_cache_entry(cache_entry)

    def load_cache(self, sub_id: SubmissionID) -> Optional[SentSubmission]:
        entry = self.db.fetch_cache_entry(sub_id.site_code, str(sub_id.submission_id))
        if entry is None:
            return None
        return SentSubmission(
            SubmissionID(entry.site_code, entry.submission_id),
            entry.is_photo,
            entry.media_id,
            entry.access_hash,
            entry.file_url,
            entry.caption,
        )
