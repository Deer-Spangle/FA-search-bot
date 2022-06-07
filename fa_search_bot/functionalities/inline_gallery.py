import logging
import re
from typing import Coroutine, List, Optional, Tuple, Union

from telethon.events import InlineQuery, StopPropagation
from telethon.tl.custom import InlineBuilder
from telethon.tl.types import InputBotInlineResult, InputBotInlineResultPhoto

from fa_search_bot.functionalities.functionalities import (
    BotFunctionality,
    _parse_inline_offset,
    answer_with_error,
)
from fa_search_bot.sites.fa_export_api import FAExportAPI, PageNotFound
from fa_search_bot.utils import gather_ignore_exceptions

logger = logging.getLogger(__name__)


class InlineGalleryFunctionality(BotFunctionality):
    INLINE_MAX = 20
    USE_CASE_GALLERY = "inline_gallery"
    USE_CASE_SCRAPS = "inline_scraps"
    PREFIX_GALLERY = ["gallery", "g"]
    PREFIX_SCRAPS = ["scraps"]
    ALL_PREFIX = PREFIX_SCRAPS + PREFIX_GALLERY

    def __init__(self, api: FAExportAPI):
        prefix_pattern = re.compile(
            "^(" + "|".join(re.escape(pref) for pref in self.ALL_PREFIX) + "):", re.I
        )
        super().__init__(InlineQuery(pattern=prefix_pattern))
        self.api = api

    @property
    def usage_labels(self) -> List[str]:
        return [self.USE_CASE_GALLERY, self.USE_CASE_SCRAPS]

    async def call(self, event: InlineQuery.Event) -> None:
        query_split = event.query.query.split(":", 1)
        offset = event.query.offset
        logger.info("Got an inline query, page=%s", offset)
        if len(query_split) != 2 or query_split[0].lower() not in self.ALL_PREFIX:
            return
        prefix, username = query_split
        folder = "gallery"
        if prefix in self.PREFIX_SCRAPS:
            folder = "scraps"
            self.usage_counter.labels(function=self.USE_CASE_SCRAPS).inc()
        else:
            self.usage_counter.labels(function=self.USE_CASE_GALLERY).inc()
        # Get results and next offset
        results, next_offset = await self._gallery_query_results(
            event, folder, username, offset
        )
        # Await results while ignoring exceptions
        results = await gather_ignore_exceptions(results)
        logger.info(f"There are {len(results)} results.")
        # Send results
        await event.answer(
            results,
            next_offset=str(next_offset) if next_offset else None,
            gallery=True,
        )
        raise StopPropagation

    async def _gallery_query_results(
            self, event: InlineQuery.Event, folder: str, username: str, offset: str
    ) -> Tuple[
        List[
            Coroutine[
                None, None, Union[InputBotInlineResult, InputBotInlineResultPhoto]
            ]
        ],
        Optional[str],
    ]:
        # Parse offset to page and skip
        page, skip = _parse_inline_offset(offset)
        # Try and get results
        try:
            results = await self._create_user_folder_results(
                event.builder, username, folder, page
            )
        except PageNotFound:
            logger.warning("User not found for inline gallery query")
            await answer_with_error(
                event,
                "User does not exist.",
                f'FurAffinity user does not exist by the name: "{username}".',
            )
            raise StopPropagation
        # If no results, send error
        if len(results) == 0:
            if offset:
                return [], None
            await answer_with_error(
                event,
                f"Nothing in {folder}.",
                f'There are no submissions in {folder} for user "{username}".',
            )
            raise StopPropagation
        # Handle paging of big result lists
        return self._page_results(results, page, skip)

    def _page_results(self, results: List, page: int, skip: int) -> Tuple[List, str]:
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

    async def _create_user_folder_results(
            self, builder: InlineBuilder, username: str, folder: str, page: int
    ) -> List[Coroutine[None, None, InputBotInlineResultPhoto]]:
        return [
            x.to_inline_query_result(builder)
            for x in await self.api.get_user_folder(username, folder, page)
        ]
