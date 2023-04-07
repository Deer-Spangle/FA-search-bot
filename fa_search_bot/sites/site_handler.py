from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from fa_search_bot.sites.sent_submission import SentSubmission
from fa_search_bot.sites.site_link import SiteLink
from fa_search_bot.sites.submission_id import SubmissionID

if TYPE_CHECKING:
    from re import Pattern
    from typing import List, Optional, Union, Awaitable

    from telethon import TelegramClient
    from telethon.tl.custom import InlineBuilder
    from telethon.tl.types import InputBotInlineMessageID, InputBotInlineResultPhoto, TypeInputPeer

logger = logging.getLogger(__name__)


class HandlerException(Exception):
    pass


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
    def find_links_in_str(self, haystack: str) -> List[SiteLink]:
        raise NotImplementedError

    @abstractmethod
    async def get_submission_id_from_link(self, link: SiteLink) -> Optional[SubmissionID]:
        raise NotImplementedError

    @abstractmethod
    def link_for_submission(self, submission_id: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def send_submission(
        self,
        submission_id: str,
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
        self, submission_id: SubmissionID, builder: InlineBuilder
    ) -> InputBotInlineResultPhoto:
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
