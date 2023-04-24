from __future__ import annotations
import dataclasses
import logging
from typing import Union, TYPE_CHECKING, Optional

import telethon.tl.patched
from prometheus_client import Counter
from telethon import events, Button, TelegramClient
from telethon.tl.types import (
    Photo,
    InputPhoto,
    InputDocument,
    InputBotInlineResultPhoto,
    InputBotInlineMessageID,
    TypeInputPeer,
)


if TYPE_CHECKING:
    from telethon.tl.custom import InlineBuilder

    from fa_search_bot.sites.submission_id import SubmissionID

logger = logging.getLogger(__name__)


sent_from_cache = Counter(
    "fasearchbot_sentsubmission_sent_from_cache_total",
    "Total number of messages sent from cache",
    labelnames=["site_code"],
)


@dataclasses.dataclass
class SentSubmission:
    sub_id: SubmissionID
    is_photo: bool
    media_id: int
    access_hash: int
    file_url: Optional[str]
    caption: str
    full_image: bool

    @classmethod
    def from_resp(
        cls,
        sub_id: SubmissionID,
        resp: Union[telethon.tl.patched.Message, bool],
        file_url: str,
        caption: str,
    ) -> Optional["SentSubmission"]:
        # When editing an image sent via inline query, telegram responds with bool instead of message
        if isinstance(resp, bool):
            return None
        # Build the sent message object to cache
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
            True,
        )

    @classmethod
    def from_inline_result(
        cls,
        sub_id: SubmissionID,
        inline_photo: InputBotInlineResultPhoto,
    ) -> "SentSubmission":
        return cls(
            sub_id,
            True,
            inline_photo.photo.id,
            inline_photo.photo.access_hash,
            None,
            inline_photo.send_message.message,
            False,
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
            sent_from_cache.labels(site_code=self.sub_id.site_code).inc()
            return True
        except Exception as e:
            logger.warning("Failed to reply from cache due to exception. Submission ID: %s", self.sub_id, exc_info=e)
            return False

    async def try_to_edit(self, client: TelegramClient, msg_id: InputBotInlineMessageID) -> bool:
        try:
            input_media = self.to_input_media()
            await client.edit_message(
                entity=msg_id,
                file=input_media,
                message=self.caption,
                parse_mode="html",
            )
            sent_from_cache.labels(site_code=self.sub_id.site_code).inc()
            return True
        except Exception as e:
            logger.warning("Failed to edit from cache due to exception. Submission ID: %s", self.sub_id, exc_info=e)
            return False

    async def try_to_send(self, client: TelegramClient, chat: TypeInputPeer, *, prefix: str = None) -> bool:
        message = self.caption
        if prefix:
            message = prefix + "\n" + self.caption
        try:
            input_media = self.to_input_media()
            await client.send_message(
                entity=chat,
                file=input_media,
                message=message,
                parse_mode="html",
            )
            sent_from_cache.labels(site_code=self.sub_id.site_code).inc()
            return True
        except Exception as e:
            logger.warning("Failed to send from cache due to exception. Submission ID: %s", self.sub_id, exc_info=e)
            return False

    async def as_inline_result(self, builder: InlineBuilder) -> InputBotInlineResultPhoto:
        return await builder.photo(
            file=self.to_input_media(),
            id=f"{self.sub_id.site_code}:{self.sub_id.submission_id}",
            text=self.caption,
            # Button is required such that the bot can get a callback with the message id, and edit it later.
            buttons=[Button.inline("⏳ Optimising", f"neaten_me:{self.sub_id.site_code}:{self.sub_id.submission_id}")],
        )
