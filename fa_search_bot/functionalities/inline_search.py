from __future__ import annotations

import logging
from typing import TYPE_CHECKING, TypeVar

from telethon.events import InlineQuery, StopPropagation

from fa_search_bot.functionalities.functionalities import BotFunctionality, _parse_inline_offset, answer_with_error

if TYPE_CHECKING:
    from typing import List, Optional, Tuple

    from telethon.tl.types import InputBotInlineResultPhoto

    from fa_search_bot.sites.handler_group import HandlerGroup

logger = logging.getLogger(__name__)
T = TypeVar("T")


class InlineSearchFunctionality(BotFunctionality):
    INLINE_MAX = 20
    USE_CASE_SEARCH = "inline_search"
    USE_CASE_E621 = "inline_e621"
    PREFIX_E621 = ["e621", "e6", "e"]

    def __init__(self, handlers: HandlerGroup):
        super().__init__(InlineQuery())
        self.handlers = handlers
        self.default_handler = handlers.default

    @property
    def usage_labels(self) -> List[str]:
        return [self.USE_CASE_SEARCH, self.USE_CASE_E621]

    async def call(self, event: InlineQuery.Event) -> None:
        query = event.query.query
        offset = event.query.offset
        logger.info("Got an inline query, page=%s", offset)
        if query.strip() == "":
            await event.answer([])
            raise StopPropagation
        # Get results and next offset
        self.usage_counter.labels(function=self.USE_CASE_SEARCH).inc()
        results, next_offset = await self._search_query_results(event, query, offset)
        logger.info(f"There are {len(results)} results.")
        # Send results
        await event.answer(
            results,
            next_offset=str(next_offset) if next_offset else None,
            gallery=True,
        )
        raise StopPropagation

    def _page_results(self, results: List[T], page: int, skip: Optional[int]) -> Tuple[List[T], str]:
        next_offset = str(page + 1)
        if skip:
            results = results[skip:]
        if len(results) > self.INLINE_MAX:
            results = results[: self.INLINE_MAX]
            if skip:
                skip += self.INLINE_MAX
            else:
                skip = self.INLINE_MAX
            next_offset = f"{page}:{skip}"
        return results, next_offset

    async def _search_query_results(
        self, event: InlineQuery.Event, query: str, offset: str
    ) -> Tuple[List[InputBotInlineResultPhoto], Optional[str]]:
        page, skip = _parse_inline_offset(offset)
        results = await self.handlers.answer_search(query, event, page)
        if len(results) == 0:
            if offset:
                return [], None
            msg = f'No results for search "{query}".'
            await answer_with_error(event, "No results found.", msg)
            raise StopPropagation
        return self._page_results(results, page, skip)
