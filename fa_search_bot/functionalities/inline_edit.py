from telethon import TelegramClient
from telethon.events import Raw, CallbackQuery
from telethon.tl.types import UpdateBotInlineSend

from fa_search_bot.functionalities.functionalities import BotFunctionality
from fa_search_bot.sites.fa_export_api import FAExportAPI
from fa_search_bot.sites.fa_handler import FAHandler


class InlineEditFunctionality(BotFunctionality):

    def __init__(self, api: FAExportAPI, client: TelegramClient):
        super().__init__(Raw(UpdateBotInlineSend))
        self.handler = FAHandler(api)
        self.client = client

    async def call(self, event: UpdateBotInlineSend) -> None:
        sub_id = int(event.id)
        msg_id = event.msg_id
        await self.handler.send_submission(sub_id, self.client, msg_id, edit=True)


class InlineEditButtonPress(BotFunctionality):

    def __init__(self, api: FAExportAPI):
        super().__init__(CallbackQuery(pattern="^neaten_me:"))
        self.handler = FAHandler(api)

    async def call(self, event: CallbackQuery) -> None:
        sub_id = event.data.encode().removeprefix("neaten_me:")
        msg_id = event.original_update.msg_id
        await self.handler.send_submission(sub_id, event.client, msg_id, edit=True)
