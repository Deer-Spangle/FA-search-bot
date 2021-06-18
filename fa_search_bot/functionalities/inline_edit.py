import logging
from typing import Dict

from telethon import TelegramClient
from telethon.events import Raw, CallbackQuery
from telethon.tl.types import UpdateBotInlineSend

from fa_search_bot.functionalities.functionalities import BotFunctionality
from fa_search_bot.sites.site_handler import SiteHandler

usage_logger = logging.getLogger("usage")
logger = logging.getLogger(__name__)


class InlineEditFunctionality(BotFunctionality):

    def __init__(self, handlers: Dict[str, SiteHandler], client: TelegramClient):
        super().__init__(Raw(UpdateBotInlineSend))
        self.handlers = handlers
        self.client = client

    async def call(self, event: UpdateBotInlineSend) -> None:
        usage_logger.info("Updating inline result")
        id_split = event.id.split(":")
        site_id = "fa"
        if len(id_split) == 2:
            site_id = id_split[0]
        sub_id = int(id_split[-1])
        handler = self.handlers.get(site_id)
        if handler is None:
            logger.error("Unrecognised site ID in result callback: %s", site_id)
            return
        msg_id = event.msg_id
        logger.debug("Got an inline result send event. site_id=%s, sub_id=%s, msg_id=%s", site_id, sub_id, msg_id)
        await handler.send_submission(sub_id, self.client, msg_id, edit=True)


class InlineEditButtonPress(BotFunctionality):

    def __init__(self, handlers: Dict[str, SiteHandler]):
        super().__init__(CallbackQuery(pattern="^neaten_me:"))
        self.handlers = handlers

    async def call(self, event: CallbackQuery) -> None:
        data = event.data.decode()
        if not data.startswith("neaten_me:"):
            return
        usage_logger.info("Inline result update button clicked")
        data_split = data.split(":")
        sub_id = int(data_split[-1])
        site_id = "fa"
        if len(data_split) == 3:
            site_id = data_split[-2]
        msg_id = event.original_update.msg_id
        handler = self.handlers.get(site_id)
        if handler is None:
            logger.error("Unrecognised site ID in button callback: %s", site_id)
            return
        logger.debug("Optimise button pressed for site_id=%s sub_id=%s msg_id=%s", site_id, sub_id, msg_id)
        await handler.send_submission(sub_id, event.client, msg_id, edit=True)
