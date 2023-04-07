from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from telethon.events import CallbackQuery, Raw
from telethon.tl.types import UpdateBotInlineSend

from fa_search_bot.functionalities.functionalities import BotFunctionality

if TYPE_CHECKING:
    from typing import Dict, List

    from telethon import TelegramClient

    from fa_search_bot.sites.site_handler import SiteHandler

logger = logging.getLogger(__name__)


class InlineEditFunctionality(BotFunctionality):
    def __init__(self, handlers: Dict[str, SiteHandler], client: TelegramClient):
        super().__init__(Raw(UpdateBotInlineSend))
        self.handlers = handlers
        self.client = client

    @property
    def usage_labels(self) -> List[str]:
        return ["inline_edit"]

    async def call(self, event: UpdateBotInlineSend) -> None:
        self.usage_counter.labels(function="inline_edit").inc()
        sub_id = SubmissionID.from_inline_code(event.id)
        handler = self.handlers.get(site_id)
        if handler is None:
            logger.error("Unrecognised site ID in result callback: %s", site_id)
            return
        msg_id = event.msg_id
        logger.debug(
            "Got an inline result send event. sub_id=%s, msg_id=%s",
            sub_id,
            msg_id,
        )
        await handler.send_submission(sub_id.submission_id, self.client, msg_id, edit=True)


class InlineEditButtonPress(BotFunctionality):
    def __init__(self, handlers: Dict[str, SiteHandler]):
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
        data_split = data.split(":")
        sub_id = data_split[-1]
        site_id = "fa"
        if len(data_split) == 3:
            site_id = data_split[-2]
        msg_id = event.original_update.msg_id
        handler = self.handlers.get(site_id)
        if handler is None:
            logger.error("Unrecognised site ID in button callback: %s", site_id)
            return
        logger.debug(
            "Optimise button pressed for site_id=%s sub_id=%s msg_id=%s",
            site_id,
            sub_id,
            msg_id,
        )
        await handler.send_submission(sub_id, event.client, msg_id, edit=True)
