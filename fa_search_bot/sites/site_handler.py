from abc import ABC, abstractmethod
from re import Pattern
from typing import List, Union, Optional, Coroutine

from telethon import TelegramClient
from telethon.tl.custom import InlineBuilder
from telethon.tl.types import TypeInputPeer, InputBotInlineMessageID, InputBotInlineResultPhoto


class HandlerException(Exception):
    pass


class SiteHandler(ABC):

    @property
    @abstractmethod
    def link_regex(self) -> Pattern:
        pass

    @abstractmethod
    def find_links_in_str(self, haystack: str) -> List[str]:
        pass

    @abstractmethod
    async def get_submission_id_from_link(self, link: str) -> int:
        pass

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
        pass

    @abstractmethod
    def is_valid_submission_id(self, example: str) -> bool:
        pass

    @abstractmethod
    async def submission_as_answer(
            self,
            submission_id: Union[int, str],
            builder: InlineBuilder
    ) -> Coroutine[None, None, InputBotInlineResultPhoto]:
        pass
