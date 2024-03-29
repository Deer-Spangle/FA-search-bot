from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from prometheus_client import Summary
from telethon.events import InlineQuery, StopPropagation
from telethon.tl.custom import InlineBuilder

from fa_search_bot.functionalities.functionalities import BotFunctionality, _parse_inline_offset, answer_with_error
from fa_search_bot.sites.sendable import InlineSendable
from fa_search_bot.sites.sent_submission import SentSubmission
from fa_search_bot.submission_cache import SubmissionCache
from fa_search_bot.utils import gather_ignore_exceptions

if TYPE_CHECKING:
    from typing import List, Optional, Tuple

    from telethon.tl.types import InputBotInlineResultPhoto

    from fa_search_bot.sites.handler_group import HandlerGroup

logger = logging.getLogger(__name__)

inline_search_results = Summary(
    "fasearchbot_inline_search_results_count",
    "Number of inline results sent via the inline search",
    labelnames=["source"],
)


class InlineSearchFunctionality(BotFunctionality):
    INLINE_MAX = 20
    INLINE_FRESH = 5
    USE_CASE_SEARCH = "inline_search"
    LABEL_SOURCE_CACHE = "cache"
    LABEL_SOURCE_FRESH = "fresh"
    LABEL_SOURCE_TOTAL = "total"

    def __init__(self, handlers: HandlerGroup, cache: SubmissionCache):
        super().__init__(InlineQuery())
        self.handlers = handlers
        self.cache = cache
        inline_search_results.labels(source=self.LABEL_SOURCE_CACHE)
        inline_search_results.labels(source=self.LABEL_SOURCE_FRESH)
        inline_search_results.labels(source=self.LABEL_SOURCE_TOTAL)

    @property
    def usage_labels(self) -> List[str]:
        return [self.USE_CASE_SEARCH]

    async def call(self, event: InlineQuery.Event) -> None:
        query = event.query.query
        offset = event.query.offset
        logger.info("Got an inline search query, page=%s", offset)
        if query.strip() == "":
            await event.answer([])
            raise StopPropagation
        # Get results and next offset
        self.usage_counter.labels(function=self.USE_CASE_SEARCH).inc()
        results, next_offset = await self._search_query_results(event, query, offset)
        logger.info(f"There are {len(results)} results.")
        # If no results, and no offset, return an error
        if len(results) == 0:
            if not offset:
                msg = f'No results for search "{query}".'
                await answer_with_error(event, "No results found.", msg)
                raise StopPropagation
        # Send results
        await event.answer(
            results,
            next_offset=next_offset,
            gallery=True,
        )
        raise StopPropagation

    async def _search_query_results(
        self, event: InlineQuery.Event, query: str, offset: str
    ) -> Tuple[List[InputBotInlineResultPhoto], Optional[str]]:
        page, skip = _parse_inline_offset(offset)
        skip = skip or 0
        # Get list of inline sendables
        sendables = await self.handlers.search(query, page)
        if not sendables:
            return [], None
        # Cut at offset
        sendables = sendables[skip:]
        # Gather new results
        result_coros = []
        fresh_results = 0
        while len(result_coros) < self.INLINE_MAX and fresh_results < self.INLINE_FRESH:
            # If none left in page, fetch the next page
            if not sendables:
                page += 1
                skip = 0
                sendables = await self.handlers.search(query, page)
                # If next page is empty, return from loop
                if not sendables:
                    break
            # Pop submission from list and check cache
            sendable = sendables.pop(0)
            skip += 1
            cache_entry = self.cache.load_cache(sendable.submission_id, allow_inline=True)
            if cache_entry:
                result_coros.append(cache_entry.as_inline_result(event.builder))
            else:
                result_coros.append(self._send_fresh_result(event.builder, sendable))
                fresh_results += 1
        # Record some metrics
        inline_search_results.labels(source=self.LABEL_SOURCE_TOTAL).observe(len(result_coros))
        inline_search_results.labels(source=self.LABEL_SOURCE_FRESH).observe(fresh_results)
        inline_search_results.labels(source=self.LABEL_SOURCE_CACHE).observe(len(result_coros) - fresh_results)
        # Await all coros to send results and new offset
        return await gather_ignore_exceptions(result_coros), f"{page}:{skip}"

    async def _send_fresh_result(
            self,
            builder: InlineBuilder,
            sendable: InlineSendable
    ) -> InputBotInlineResultPhoto:
        sub_id = sendable.submission_id
        inline_photo = await sendable.to_inline_query_result(builder)
        # Save to cache
        sent_sub = SentSubmission.from_inline_result(sub_id, inline_photo)
        self.cache.save_cache(sent_sub)
        return inline_photo
