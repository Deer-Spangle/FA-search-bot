from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from telethon.events import CallbackQuery, Raw
from telethon.tl.types import UpdateBotInlineSend

from fa_search_bot.functionalities.functionalities import BotFunctionality
from fa_search_bot.sites.furaffinity.fa_export_api import PageNotFound
from fa_search_bot.sites.submission_id import SubmissionID

if TYPE_CHECKING:
    from typing import List

    from telethon import TelegramClient

    from fa_search_bot.sites.handler_group import HandlerGroup

logger = logging.getLogger(__name__)


class InlineEditFunctionality(BotFunctionality):
    def __init__(self, handlers: HandlerGroup, client: TelegramClient):
        super().__init__(Raw(UpdateBotInlineSend))
        self.handlers = handlers
        self.client = client

    @property
    def usage_labels(self) -> List[str]:
        return ["inline_edit"]

    async def call(self, event: UpdateBotInlineSend) -> None:
        self.usage_counter.labels(function="inline_edit").inc()
        sub_id = SubmissionID.from_inline_code(event.id)
        msg_id = event.msg_id
        logger.debug(
            "Got an inline result send event. sub_id=%s, msg_id=%s",
            sub_id,
            msg_id,
        )
        try:
            await self.handlers.edit_submission(sub_id, self.client, msg_id)
        except PageNotFound as e:
            logger.error("Failed to edit inline query response: ", exc_info=e)


class InlineEditButtonPress(BotFunctionality):
    def __init__(self, handlers: HandlerGroup):
        super().__init__(CallbackQuery(pattern="^neaten_me:"))
        self.handlers = handlers

    @property
    def usage_labels(self) -> List[str]:
        return ["inline_edit_button"]

    async def call(self, event: CallbackQuery) -> None:
        data = event.data.decode()
        if not data.startswith("neaten_me:"):
            return
        self.usage_counter.labels(function="inline_edit_button").inc()
        sub_id = SubmissionID.from_inline_code(data.removeprefix("neaten_me:"))
        msg_id = event.original_update.msg_id
        logger.debug(
            "Optimise button pressed for sub_id=%s msg_id=%s",
            sub_id,
            msg_id,
        )
        await self.handlers.edit_submission(sub_id, event.client, msg_id)
