import logging
from typing import List

from telethon.events import InlineQuery, StopPropagation
from telethon.tl.types import InputBotInlineResultPhoto

from fa_search_bot.functionalities.functionalities import BotFunctionality
from fa_search_bot.utils import gather_ignore_exceptions
from fa_search_bot.sites.fa_export_api import FAExportAPI, APIException
from fa_search_bot.sites.fa_handler import FAHandler

usage_logger = logging.getLogger("usage")
logger = logging.getLogger(__name__)


class InlineNeatenFunctionality(BotFunctionality):

    def __init__(self, api: FAExportAPI) -> None:
        super().__init__(InlineQuery())
        self.handler = FAHandler(api)

    async def call(self, event: InlineQuery.Event):
        query = event.query.query
        query_clean = query.strip().lower()
        # Check if it's a submission ID
        if self.handler.is_valid_submission_id(query_clean):
            await self._answer_id_query(event, query_clean)
        # Check if it's a link
        link_matches = self.handler.find_links_in_str(query_clean)
        if link_matches:
            await self._answer_link_query(event, link_matches)
        # Otherwise, pass and let inline functionality handle it
        pass

    async def _answer_id_query(self, event: InlineQuery.Event, submission_id: str) -> None:
        try:
            result_future = await self.handler.submission_as_answer(submission_id, event.builder)
            result = await result_future
            if result:
                usage_logger.info("Inline submission ID query")
                logger.info("Sending inline ID query result")
                await event.answer([result], gallery=isinstance(result, InputBotInlineResultPhoto))
                raise StopPropagation
        except APIException:
            logger.debug("Inline id query could not find result")
            pass

    async def _answer_link_query(self, event: InlineQuery.Event, links: List[str]) -> None:
        submission_ids = await gather_ignore_exceptions([
            self.handler.get_submission_id_from_link(link) for link in links
        ])
        results = await gather_ignore_exceptions([
            self.handler.submission_as_answer(sub_id, event.builder) for sub_id in submission_ids
        ])
        results = await gather_ignore_exceptions(results)
        if results:
            usage_logger.info("Inline submission link query")
            logger.info("Sending inline link query results")
            await event.answer(results, gallery=isinstance(results[0], InputBotInlineResultPhoto))
            raise StopPropagation
