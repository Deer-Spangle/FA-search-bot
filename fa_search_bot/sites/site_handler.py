import typing
from abc import ABC, abstractmethod
from re import Pattern
import typing
from typing import List, Union, Optional, Coroutine

from telethon import TelegramClient
from telethon.tl.custom import InlineBuilder
from telethon.tl.types import TypeInputPeer, InputBotInlineMessageID, InputBotInlineResultPhoto

if typing.TYPE_CHECKING:
    from fa_search_bot.sites.sendable import Sendable


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
            edit: bool = False
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_valid_submission_id(self, example: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def submission_as_answer(
            self,
            submission_id: Union[int, str],
            builder: InlineBuilder
    ) -> Coroutine[None, None, InputBotInlineResultPhoto]:
        raise NotImplementedError

    @abstractmethod
    async def get_search_results(
            self,
            query: str,
            page: int
    ) -> List["Sendable"]:
        raise NotImplementedError
