import random
from typing import Optional, List, Dict

from fa_search_bot.sites.sent_submission import SentSubmission
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.submission_cache import SubmissionCache
from fa_search_bot.tests.util.mock_export_api import _random_image_id, _random_string


class MockSubmissionCache(SubmissionCache):
    def __init__(self):
        super().__init__(None)
        self.sent_storage: Dict[SubmissionID, SentSubmission] = {}

    def save_cache(self, sent_submission: Optional[SentSubmission]) -> None:
        if sent_submission is None:
            return None
        if sent_submission.save_cache:
            self.sent_storage[sent_submission.sub_id] = sent_submission

    def load_cache(self, sub_id: SubmissionID, *, allow_inline: bool = False) -> Optional[SentSubmission]:
        sent_sub = self.sent_storage.get(sub_id)
        if sent_sub is None:
            return None
        if allow_inline or sent_sub.full_image:
            return sent_sub
        return None

    @classmethod
    def with_submission_ids(cls, sub_ids: List[SubmissionID], *, username: str = None) -> "MockSubmissionCache":
        cache = cls()
        for sub_id in sub_ids:
            cache.save_cache(mock_sent_submission(sub_id, username=username))
        return cache


def mock_sent_submission(
        sub_id: SubmissionID,
        *,
        is_photo: bool = True,
        media_id: int = None,
        access_hash: int = None,
        file_url: str = None,
        username: str = None,
        caption: str = None,
        full_image: bool = True,
        save_cache: bool = True,
) -> SentSubmission:
    if media_id is None:
        media_id = random.randint(1_000_000, 9_999_999)
    if access_hash is None:
        access_hash = random.randint(-9_999_999, 9_999_999)
    if file_url is None:
        if username is None:
            username = _random_string()
        image_id = _random_image_id(int(sub_id.submission_id))
        file_url = f"https://d.furaffinity.net/art/{username}/{image_id}/{image_id}.{username}_{_random_string()}.jpg"
    if not full_image:
        file_url = None
    if caption is None:
        caption = f"https://furaffinity.net/view/{sub_id.submission_id}/"
    return SentSubmission(
        sub_id,
        is_photo,
        media_id,
        access_hash,
        file_url,
        caption,
        full_image,
        save_cache,
    )
