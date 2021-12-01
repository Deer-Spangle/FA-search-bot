import logging
from typing import Tuple, List, Optional, Coroutine

from telethon.events import InlineQuery, StopPropagation
from telethon.tl.custom import InlineBuilder
from telethon.tl.types import InputBotInlineResultPhoto, InputBotInlineResult

from fa_search_bot.sites.e621_handler import E621Handler
from fa_search_bot.sites.fa_export_api import FAExportAPI
from fa_search_bot.functionalities.functionalities import BotFunctionality, answer_with_error
from fa_search_bot.utils import gather_ignore_exceptions

logger = logging.getLogger(__name__)


class InlineSearchFunctionality(BotFunctionality):
    INLINE_MAX = 20
    USE_CASE_SEARCH = "inline_search"
    USE_CASE_E621 = "inline_e621"
    PREFIX_E621 = ["e621", "e6", "e"]

    def __init__(self, api: FAExportAPI, e621: E621Handler):
        super().__init__(InlineQuery())
        self.api = api
        self.e621 = e621

    @property
    def usage_labels(self) -> List[str]:
        return [self.USE_CASE_SEARCH, self.USE_CASE_E621]

    async def call(self, event: InlineQuery.Event):
        query = event.query.query
        offset = event.query.offset
        logger.info("Got an inline query, page=%s", offset)
        if query.strip() == "":
            await event.answer([])
            raise StopPropagation
        # Get results and next offset
        self.usage_counter.labels(function=self.USE_CASE_SEARCH).inc()
        results, next_offset = await self._search_query_results(event.builder, query, offset)
        # Await results while ignoring exceptions
        results = await gather_ignore_exceptions(results)
        logger.info(f"There are {len(results)} results.")
        # Figure out whether to display as gallery
        if len(results) == 0:
            gallery = bool(offset)
        else:
            gallery = isinstance(results[0], InputBotInlineResultPhoto)
        # Send results
        await event.answer(
            results,
            next_offset=str(next_offset) if next_offset else None,
            gallery=gallery,
        )
        raise StopPropagation

    def _parse_offset(self, offset: str) -> Tuple[int, int]:
        if offset == "":
            page, skip = 1, None
        elif ":" in offset:
            page, skip = (int(x) for x in offset.split(":", 1))
        else:
            page, skip = int(offset), None
        return page, skip

    def _page_results(self, results: List, page: int, skip: int) -> Tuple[List, str]:
        next_offset = str(page + 1)
        if skip:
            results = results[skip:]
        if len(results) > self.INLINE_MAX:
            results = results[:self.INLINE_MAX]
            if skip:
                skip += self.INLINE_MAX
            else:
                skip = self.INLINE_MAX
            next_offset = f"{page}:{skip}"
        return results, next_offset

    async def _search_query_results(
            self,
            event: InlineQuery.Event,
            query: str,
            offset: str
    ) -> Tuple[List[Coroutine[None, None, InputBotInlineResult]], Optional[str]]:
        page, skip = self._parse_offset(offset)
        query_clean = query.strip().lower()
        results = await self._create_inline_search_results(event.builder, query_clean, page)
        if len(results) == 0:
            if offset:
                return [], None
            msg = f"No results for search \"{query}\"."
            await answer_with_error(event, "No results found.", msg)
            raise StopPropagation
        return self._page_results(results, page, skip)

    async def _create_inline_search_results(
            self,
            builder: InlineBuilder,
            query_clean: str,
            page: int
    ) -> List[Coroutine[None, None, InputBotInlineResultPhoto]]:
        return [
            x.to_inline_query_result(builder)
            for x
            in await self.api.get_search_results(query_clean, page)
        ]

    async def _create_e621_search_results(
            self,
            builder: InlineBuilder,
            query_clean: str,
            page: int
    ) -> List[Coroutine[None, None, InputBotInlineResultPhoto]]:
        return [
            x.to_inline_query_result(builder)
            for x
            in await self.e621.get_search_results(query_clean, page)
        ]
