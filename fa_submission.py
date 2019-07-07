import re
from abc import ABC
from typing import Dict

import requests
import telegram
from telegram import InlineQueryResultPhoto


class CantSendFileType(Exception):
    pass


class FASubmission(ABC):
    EXTENSIONS_DOCUMENT = ["doc", "docx", "rtf", "txt", "odt", "mid", "wav", "mpeg"]
    EXTENSIONS_AUTO_DOCUMENT = ["gif", "pdf"]
    EXTENSIONS_AUDIO = ["mp3"]
    EXTENSIONS_PHOTO = ["jpg", "jpeg", "png"]
    EXTENSIONS_ERROR = ["swf"]

    SIZE_LIMIT_IMAGE = 5 * 1000 ** 2  # Maximum 5MB image size on telegram
    SIZE_LIMIT_DOCUMENT = 20 * 1000 ** 2  # Maximum 20MB document size on telegram

    def __init__(self, submission_id: str) -> None:
        self.submission_id = submission_id
        self.link = f"https://furaffinity.net/view/{submission_id}/"

    @staticmethod
    def from_short_dict(short_dict: Dict[str, str]) -> 'FASubmissionShort':
        submission_id = short_dict['id']
        thumbnail_url = FASubmission.make_thumbnail_bigger(short_dict['thumbnail'])
        if "fav_id" in short_dict:
            new_submission = FASubmissionShortFav(submission_id, thumbnail_url, short_dict['fav_id'])
        else:
            new_submission = FASubmissionShort(submission_id, thumbnail_url)
        return new_submission

    @staticmethod
    def from_full_dict(full_dict: Dict[str, str]) -> 'FASubmissionFull':
        submission_id = FASubmission.id_from_link(full_dict['link'])
        thumbnail_url = FASubmission.make_thumbnail_bigger(full_dict['thumbnail'])
        download_url = full_dict['download']
        full_image_url = full_dict['full']
        new_submission = FASubmissionFull(submission_id, thumbnail_url, download_url, full_image_url)
        return new_submission

    @staticmethod
    def make_thumbnail_bigger(thumbnail_url: str) -> str:
        return re.sub('@[0-9]+-', '@1600-', thumbnail_url)

    @staticmethod
    def make_thumbnail_smaller(thumbnail_url: str) -> str:
        return re.sub('@[0-9]+-', '@300-', thumbnail_url)

    @staticmethod
    def id_from_link(link: str) -> str:
        return re.search('view/([0-9]+)', link).group(1)

    @staticmethod
    def _get_file_size(url: str) -> int:
        resp = requests.head(url)
        return int(resp.headers['content-length'])


class FASubmissionShort(FASubmission):

    def __init__(self, submission_id: str, thumbnail_url: str) -> None:
        super().__init__(submission_id)
        self.thumbnail_url = thumbnail_url

    def to_inline_query_result(self) -> InlineQueryResultPhoto:
        return InlineQueryResultPhoto(
            id=self.submission_id,
            photo_url=self.thumbnail_url,
            thumb_url=FASubmission.make_thumbnail_smaller(self.thumbnail_url),
            caption=self.link
        )


class FASubmissionShortFav(FASubmissionShort):

    def __init__(self, submission_id: str, thumbnail_url: str, fav_id: str) -> None:
        super().__init__(submission_id, thumbnail_url)
        self.fav_id = fav_id


class FASubmissionFull(FASubmissionShort):

    def __init__(self, submission_id: str, thumbnail_url: str, download_url: str, full_image_url: str) -> None:
        super().__init__(submission_id, thumbnail_url)
        self.download_url = download_url
        self.full_image_url = full_image_url
        self._download_file_size = None

    @property
    def download_file_size(self) -> int:
        if self._download_file_size is None:
            self._download_file_size = FASubmission._get_file_size(self.download_url)
        return self._download_file_size

    def send_message(self, bot, chat_id: int, reply_to: int = None) -> None:
        ext = self.download_url.split(".")[-1].lower()
        # Handle photos
        if ext in FASubmission.EXTENSIONS_PHOTO:
            if self.download_file_size > self.SIZE_LIMIT_IMAGE:
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
        if ext in FASubmission.EXTENSIONS_DOCUMENT or self.download_file_size > self.SIZE_LIMIT_DOCUMENT:
            bot.send_photo(
                chat_id=chat_id,
                photo=self.full_image_url,
                caption=f"{self.link}\n[Direct download]({self.download_url})",
                reply_to_message_id=reply_to,
                parse_mode=telegram.ParseMode.MARKDOWN
            )
            return
        # Handle gifs, and pdfs, which can be sent as documents
        if ext in FASubmission.EXTENSIONS_AUTO_DOCUMENT:
            bot.send_document(
                chat_id=chat_id,
                document=self.download_url,
                caption=self.link,
                reply_to_message_id=reply_to
            )
            return
        # Handle audio
        if ext in FASubmission.EXTENSIONS_AUDIO:
            bot.send_audio(
                chat_id=chat_id,
                audio=self.download_url,
                caption=self.link,
                reply_to_message_id=reply_to
            )
            return
        # Handle known error extensions
        if ext in FASubmission.EXTENSIONS_ERROR:
            raise CantSendFileType(f"I'm sorry, I can't neaten \".{ext}\" files.")
        raise CantSendFileType(f"I'm sorry, I don't understand that file extension ({ext}).")
