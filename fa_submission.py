import re
from typing import Dict

import requests
import telegram
from telegram import InlineQueryResultPhoto


class CantSendFileType(Exception):
    pass


class FASubmission:

    SIZE_LIMIT_IMAGE = 5 * 1000 ** 2  # Maximum 5MB image size on telegram
    SIZE_LIMIT_DOCUMENT = 20 * 1000 ** 2  # Maximum 20MB document size on telegram

    def __init__(self, submission_id: str) -> None:
        self.submission_id = submission_id
        self.link = f"https://furaffinity.net/view/{submission_id}/"
        self._thumbnail_url = None
        self._download_url = None
        self._full_image_url = None

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
        new_submission = cls(FASubmission.id_from_link(full_dict['link']))
        new_submission.link = full_dict['link']
        new_submission._thumbnail_url = FASubmission.make_thumbnail_bigger(full_dict['thumbnail'])
        new_submission._download_url = full_dict['download']
        new_submission._full_image_url = full_dict['full']
        return new_submission

    @staticmethod
    def make_thumbnail_bigger(thumbnail_url: str) -> str:
        return re.sub('@[0-9]+-', '@1600-', thumbnail_url)

    @staticmethod
    def id_from_link(link: str) -> str:
        return re.search('view/([0-9]+)', link).group(1)

    def load_full_data(self):
        pass  # TODO

    @property
    def thumbnail_url(self) -> str:
        if self._thumbnail_url is None:
            self.load_full_data()
        return self._thumbnail_url

    @property
    def download_url(self) -> str:
        if self._download_url is None:
            self.load_full_data()
        return self._download_url

    @property
    def full_image_url(self) -> str:
        if self._full_image_url is None:
            self.load_full_data()
        return self._full_image_url

    def to_inline_query_result(self) -> InlineQueryResultPhoto:
        return InlineQueryResultPhoto(
            id=self.submission_id,
            photo_url=self.thumbnail_url,  # TODO: can use full URL if certain conditions are met
            thumb_url=self.thumbnail_url,
            caption=self.link
        )

    def send_message(self, bot, chat_id, reply_to=None):
        ext = self.download_url.split(".")[-1].lower()
        document_extensions = ["doc", "docx", "rtf", "txt", "odt", "mid", "wav", "mpeg"]
        auto_document_extensions = ["gif", "pdf"]
        audio_extensions = ["mp3"]
        photo_extensions = ["jpg", "jpeg", "png"]
        error_extensions = ["swf"]
        # Handle photos
        if ext in photo_extensions:
            if _get_file_size(self.download_url) > self.SIZE_LIMIT_IMAGE:
                bot.send_photo(
                    chat_id=chat_id,
                    photo=self.thumbnail_url,
                    caption=f"{self.link}\n[Direct download]({self.download_url})",
                    reply_to_message_id=reply_to,
                    parse_mode=telegram.ParseMode.MARKDOWN
                )
                return
            bot.send_photo(
                chat_id=chat_id,
                photo=self.download_url,
                caption=self.link,
                reply_to_message_id=reply_to
            )
            return
        # Handle files telegram can't handle
        if ext in document_extensions or _get_file_size(self.download_url) > self.SIZE_LIMIT_DOCUMENT:
            bot.send_photo(
                chat_id=chat_id,
                photo=self.full_image_url,
                caption=f"{self.link}\n[Direct download]({self.download_url})",
                reply_to_message_id=reply_to,
                parse_mode=telegram.ParseMode.MARKDOWN
            )
            return
        # Handle gifs, and pdfs, which can be sent as documents
        if ext in auto_document_extensions:
            bot.send_document(
                chat_id=chat_id,
                document=self.download_url,
                caption=self.link,
                reply_to_message_id=reply_to
            )
            return
        # Handle audio
        if ext in audio_extensions:
            bot.send_audio(
                chat_id=chat_id,
                audio=self.download_url,
                caption=self.link,
                reply_to_message_id=reply_to
            )
            return
        # Handle known error extensions
        if ext in error_extensions:
            raise CantSendFileType(f"I'm sorry, I can't neaten \".{ext}\" files.")
        raise CantSendFileType(f"I'm sorry, I don't understand that file extension ({ext}).")


def _get_file_size(url):
    resp = requests.head(url)
    return int(resp.headers['content-length'])
