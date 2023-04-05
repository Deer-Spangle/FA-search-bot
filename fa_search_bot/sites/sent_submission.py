import dataclasses
import logging
from typing import Union

import telethon.tl.patched
from telethon import events
from telethon.tl.types import Photo, InputPhoto, InputDocument

from fa_search_bot.sites.submission_id import SubmissionID

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class SentSubmission:
    sub_id: SubmissionID
    is_photo: bool
    media_id: int
    access_hash: int
    file_url: str
    caption: str

    @classmethod
    def from_resp(
            cls,
            sub_id: SubmissionID,
            resp: telethon.tl.patched.Message,
            file_url: str,
            caption: str
    ) -> "SentSubmission":
        is_photo: bool = isinstance(resp.file.media, Photo)
        media_id: int = resp.file.media.id
        access_hash: int = resp.file.media.access_hash
        return cls(
            sub_id,
            is_photo,
            media_id,
            access_hash,
            file_url,
            caption,
        )

    def to_input_media(self) -> Union[InputPhoto, InputDocument]:
        return (InputPhoto if self.is_photo else InputDocument)(self.media_id, self.access_hash, b"")

    async def try_to_reply(self, event: events.NewMessage.Event) -> bool:
        try:
            input_media = self.to_input_media()
            await event.reply(
                self.caption,
                file=input_media,
                force_document=not self.is_photo,
                parse_mode="html",
            )
            return True
        except Exception as e:
            logger.warning("Failed to post from cache due to exception. Submission ID: %s", self.sub_id, exc_info=e)
            return False
