import logging
from typing import Dict, List, Optional

from telethon.events import InlineQuery, StopPropagation
from telethon.tl.types import InputBotInlineResultPhoto

from fa_search_bot.functionalities.functionalities import BotFunctionality
from fa_search_bot.sites.fa_export_api import APIException
from fa_search_bot.sites.site_handler import SiteHandler
from fa_search_bot.utils import gather_ignore_exceptions

logger = logging.getLogger(__name__)


class InlineNeatenFunctionality(BotFunctionality):
    USE_CASE_ID = "inline_neaten_id"
    USE_CASE_LINK = "inline_neaten_link"

    def __init__(self, handlers: Dict[str, SiteHandler]) -> None:
        super().__init__(InlineQuery())
        self.handlers = handlers

    @property
    def usage_labels(self) -> List[str]:
        return [self.USE_CASE_ID] + [
            f"{self.USE_CASE_LINK}_{handler.site_code}" for handler in self.handlers.values()
        ]

    async def call(self, event: InlineQuery.Event):
        query = event.query.query
        query_clean = query.strip().lower()
        # Check if it's a submission ID
        if any(handler.is_valid_submission_id(query_clean) for handler in self.handlers.values()):
            results = await self._answer_id_query(event, query_clean)
            if results:
                self.usage_counter.labels(function=f"{self.USE_CASE_ID}").inc()
                logger.info("Sending inline ID query result")
                await event.answer(results, gallery=True)
                raise StopPropagation
        # Check if it's a link
        for handler in self.handlers.values():
            link_matches = handler.find_links_in_str(query_clean)
            if link_matches:
                results = await self._answer_link_query(event, handler, link_matches)
                if results:
                    self.usage_counter.labels(function=f"{self.USE_CASE_LINK}_{handler.site_code}").inc()
                    logger.info("Sending inline link query results")
                    await event.answer(results, gallery=True)
                    raise StopPropagation
        # Otherwise, pass and let inline functionality handle it
        pass

    async def _answer_id_query(
            self,
            event: InlineQuery.Event,
            submission_id: str
    ) -> Optional[List[InputBotInlineResultPhoto]]:
        try:
            result_futures = await gather_ignore_exceptions([
                handler.submission_as_answer(submission_id, event.builder)
                for handler in self.handlers.values()
            ])
            return await gather_ignore_exceptions(result_futures)
        except APIException:
            logger.debug("Inline id query could not find result")
            pass

    async def _answer_link_query(
            self,
            event: InlineQuery.Event,
            handler: SiteHandler,
            links: List[str]
    ) -> Optional[List[InputBotInlineResultPhoto]]:
        submission_ids = await gather_ignore_exceptions([
            handler.get_submission_id_from_link(link) for link in links
        ])
        results = await gather_ignore_exceptions([
            handler.submission_as_answer(sub_id, event.builder) for sub_id in submission_ids
        ])
        return await gather_ignore_exceptions(results)
