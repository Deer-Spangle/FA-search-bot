import logging

from telethon import TelegramClient
from telethon.events import Raw, CallbackQuery
from telethon.tl.types import UpdateBotInlineSend

from fa_search_bot.functionalities.functionalities import BotFunctionality
from fa_search_bot.sites.site_handler import SiteHandler

usage_logger = logging.getLogger("usage")
logger = logging.getLogger(__name__)


class InlineEditFunctionality(BotFunctionality):

    def __init__(self, handler: SiteHandler, client: TelegramClient):
        super().__init__(Raw(UpdateBotInlineSend))
        self.handler = handler
        self.client = client

    async def call(self, event: UpdateBotInlineSend) -> None:
        usage_logger.info("Updating inline result")
        sub_id = int(event.id)
        msg_id = event.msg_id
        logger.debug("Got an inline result send event. sub_id=%s, msg_id=%s", sub_id, msg_id)
        await self.handler.send_submission(sub_id, self.client, msg_id, edit=True)


class InlineEditButtonPress(BotFunctionality):

    def __init__(self, handler: SiteHandler):
        super().__init__(CallbackQuery(pattern="^neaten_me:"))
        self.handler = handler

    async def call(self, event: CallbackQuery) -> None:
        data = event.data.decode()
        if not data.startswith("neaten_me:"):
            return
        usage_logger.info("Inline result update button clicked")
        sub_id = data.split(":", 1)[1]
        msg_id = event.original_update.msg_id
        logger.debug("Optimise button pressed for sub_id=%s msg_id=%s", sub_id, msg_id)
        await self.handler.send_submission(sub_id, event.client, msg_id, edit=True)
