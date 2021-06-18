import logging
from typing import List, Dict

from telethon.events import InlineQuery, StopPropagation
from telethon.tl.types import InputBotInlineResultPhoto

from fa_search_bot.functionalities.functionalities import BotFunctionality
from fa_search_bot.sites.site_handler import SiteHandler
from fa_search_bot.utils import gather_ignore_exceptions
from fa_search_bot.sites.fa_export_api import APIException

usage_logger = logging.getLogger("usage")
logger = logging.getLogger(__name__)


class InlineNeatenFunctionality(BotFunctionality):

    def __init__(self, handlers: Dict[str, SiteHandler]) -> None:
        super().__init__(InlineQuery())
        self.handlers = handlers

    async def call(self, event: InlineQuery.Event):
        query = event.query.query
        query_clean = query.strip().lower()
        # Check if it's a submission ID
        if any(handler.is_valid_submission_id(query_clean) for handler in self.handlers.values()):
            await self._answer_id_query(event, query_clean)
            raise StopPropagation
        # Check if it's a link
        for handler in self.handlers.values():
            link_matches = handler.find_links_in_str(query_clean)
            if link_matches:
                await self._answer_link_query(event, handler, link_matches)
                raise StopPropagation
        # Otherwise, pass and let inline functionality handle it
        pass

    async def _answer_id_query(self, event: InlineQuery.Event, submission_id: str) -> None:
        try:
            result_futures = await gather_ignore_exceptions([
                handler.submission_as_answer(submission_id, event.builder)
                for handler in self.handlers.values()
            ])
            results = await gather_ignore_exceptions(result_futures)
            if results:
                usage_logger.info("Inline submission ID query")
                logger.info("Sending inline ID query result")
                await event.answer([results], gallery=True)
        except APIException:
            logger.debug("Inline id query could not find result")
            pass

    async def _answer_link_query(self, event: InlineQuery.Event, handler: SiteHandler, links: List[str]) -> None:
        submission_ids = await gather_ignore_exceptions([
            handler.get_submission_id_from_link(link) for link in links
        ])
        results = await gather_ignore_exceptions([
            handler.submission_as_answer(sub_id, event.builder) for sub_id in submission_ids
        ])
        results = await gather_ignore_exceptions(results)
        if results:
            usage_logger.info("Inline submission link query")
            logger.info("Sending inline link query results")
            await event.answer(results, gallery=isinstance(results[0], InputBotInlineResultPhoto))
