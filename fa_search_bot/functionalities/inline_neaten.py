from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from telethon.events import InlineQuery, StopPropagation

from fa_search_bot.functionalities.functionalities import BotFunctionality
from fa_search_bot.sites.handler_group import HandlerGroup

if TYPE_CHECKING:
    from typing import List

logger = logging.getLogger(__name__)


class InlineNeatenFunctionality(BotFunctionality):
    USE_CASE_ID = "inline_neaten_id"
    USE_CASE_LINK = "inline_neaten_link"

    def __init__(self, handlers: HandlerGroup) -> None:
        super().__init__(InlineQuery())
        self.handlers = handlers

    @property
    def usage_labels(self) -> List[str]:
        return [self.USE_CASE_ID] + [f"{self.USE_CASE_LINK}_{site_code}" for site_code in self.handlers.site_codes()]

    async def call(self, event: InlineQuery.Event) -> None:
        query = event.query.query
        query_clean = query.strip().lower()
        # Check if it's a submission ID
        sub_ids = self.handlers.list_potential_submission_ids(query_clean)
        if sub_ids:
            results = await self.handlers.answer_submission_ids(sub_ids, event)
            if results:
                self.usage_counter.labels(function=f"{self.USE_CASE_ID}").inc()
                logger.info("Sending inline ID query result")
                await event.answer(results, gallery=True)
                raise StopPropagation
        # Check if it's a link
        links = self.handlers.list_potential_links(query_clean)
        if links:
            results = await self.handlers.answer_links(links, event)
            if results:
                self.usage_counter.labels(function=f"{self.USE_CASE_LINK}").inc()
                logger.info("Sending inline link query results")
                await event.answer(results, gallery=True)
                raise StopPropagation
        # Otherwise, pass and let inline functionality handle it
        pass
