import re
from typing import Dict

from telegram import InlineQueryResultPhoto


class FASubmission:

    def __init__(self, submission_id: str) -> None:
        self.submission_id = submission_id
        self.link = "https://furaffinity.net/view/{}/".format(submission_id)
        self._thumbnail_url = None
        self._full_url = None

    @classmethod
    def from_id(cls, submission_id: str) -> 'FASubmission':
        return cls(submission_id)

    @classmethod
    def from_short_dict(cls, short_dict: Dict[str, str]) -> 'FASubmission':
        new_submission = cls(short_dict['id'])
        new_submission.link = short_dict['link']
        new_submission._thumbnail_url = FASubmission.make_thumbnail_bigger(short_dict['thumbnail'])
        return new_submission

    @classmethod
    def from_full_dict(cls, full_dict: Dict[str, str]) -> 'FASubmission':
        new_submission = cls(full_dict['id'])
        new_submission.link = full_dict['link']
        new_submission._thumbnail_url = FASubmission.make_thumbnail_bigger(full_dict['thumbnail'])
        new_submission._full_url = full_dict['download']
        return new_submission

    @staticmethod
    def make_thumbnail_bigger(thumbnail_url: str) -> str:
        return re.sub('@[0-9]+-', '@1600-', thumbnail_url)

    def load_full_data(self):
        pass  # TODO

    @property
    def thumbnail_url(self) -> str:
        if self._thumbnail_url is None:
            self.load_full_data()
        return self._thumbnail_url

    def to_inline_query_result(self) -> InlineQueryResultPhoto:
        return InlineQueryResultPhoto(
            id=self.submission_id,
            photo_url=self.thumbnail_url,  # TODO: can use full URL if certain conditions are met
            thumb_url=self.thumbnail_url,
            caption=self.link
        )

    def send_message(self, bot, chat_id, reply_to=None):
        pass  # TODO
