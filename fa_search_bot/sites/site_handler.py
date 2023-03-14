from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from telethon.tl.types import Photo, InputPhoto, InputDocument

if TYPE_CHECKING:
    from re import Pattern
    from typing import List, Optional, Union, Awaitable

    from telethon import TelegramClient
    from telethon.tl.custom import InlineBuilder
    import telethon.tl.patched
    from telethon.tl.types import InputBotInlineMessageID, InputBotInlineResultPhoto, TypeInputPeer


class HandlerException(Exception):
    pass


@dataclasses.dataclass(frozen=True)
class SubmissionID:
    site_code: str
    submission_id: int


@dataclasses.dataclass
class SentSubmission:
    sub_id: SubmissionID
    is_photo: bool
    media_id: int
    access_hash: int
    file_url: str

    @classmethod
    def from_resp(cls, sub_id: SubmissionID, resp: telethon.tl.patched.Message, file_url: str) -> "SentSubmission":
        is_photo: bool = isinstance(resp.file.media, Photo)
        media_id: int = resp.file.media.id
        access_hash: int = resp.file.media.access_hash
        return cls(
            sub_id,
            is_photo,
            media_id,
            access_hash,
            file_url,
        )

    def to_input_media(self) -> Union[InputPhoto, InputDocument]:
        return (InputPhoto if self.is_photo else InputDocument)(self.media_id, self.access_hash, b"")


class SiteHandler(ABC):
    @property
    @abstractmethod
    def site_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def site_code(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def link_regex(self) -> Pattern:
        raise NotImplementedError

    @abstractmethod
    def find_links_in_str(self, haystack: str) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    async def get_submission_id_from_link(self, link: str) -> Optional[int]:
        raise NotImplementedError

    @abstractmethod
    def link_for_submission(self, submission_id: int) -> str:
        raise NotImplementedError

    @abstractmethod
    async def send_submission(
        self,
        submission_id: int,
        client: TelegramClient,
        chat: Union[TypeInputPeer, InputBotInlineMessageID],
        *,
        reply_to: Optional[int] = None,
        prefix: str = None,
        edit: bool = False,
    ) -> SentSubmission:
        raise NotImplementedError

    @abstractmethod
    def is_valid_submission_id(self, example: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def submission_as_answer(
        self, submission_id: Union[int, str], builder: InlineBuilder
    ) -> Awaitable[InputBotInlineResultPhoto]:
        raise NotImplementedError

    @property
    def search_prefixes(self) -> List[str]:
        return [
            self.site_name[0].lower(),
            self.site_code.lower(),
            self.site_name.lower(),
        ]

    @abstractmethod
    async def get_search_results(
        self, builder: InlineBuilder, query: str, page: int
    ) -> List[Awaitable[InputBotInlineResultPhoto]]:
        raise NotImplementedError
