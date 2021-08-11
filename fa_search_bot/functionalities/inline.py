import logging
from typing import Tuple, List, Union, Optional, Coroutine

from telethon.events import InlineQuery, StopPropagation
from telethon.tl.custom import InlineBuilder
from telethon.tl.types import InputBotInlineResultPhoto, InputBotInlineResult

from fa_search_bot.sites.fa_export_api import FAExportAPI, PageNotFound
from fa_search_bot.functionalities.functionalities import BotFunctionality
from fa_search_bot.utils import gather_ignore_exceptions

logger = logging.getLogger(__name__)


class InlineFunctionality(BotFunctionality):
    INLINE_MAX = 20
    USE_CASE_FAVS = "favourites"
    USE_CASE_GALLERY = "gallery"
    USE_CASE_SEARCH = "search"

    def __init__(self, api: FAExportAPI):
        super().__init__(InlineQuery())
        self.api = api
        self.usage_counter.labels(use_case=self.USE_CASE_FAVS)
        self.usage_counter.labels(use_case=self.USE_CASE_GALLERY)
        self.usage_counter.labels(use_case=self.USE_CASE_SEARCH)

    async def call(self, event: InlineQuery.Event):
        query = event.query.query
        query_clean = query.strip().lower()
        offset = event.query.offset
        logger.info("Got an inline query, page=%s", offset)
        if query_clean == "":
            await event.answer([])
            raise StopPropagation
        # Get results and next offset
        if any(query_clean.startswith(x) for x in ["favourites:", "favs:", "favorites:"]):
            self.usage_counter.labels(use_case=self.USE_CASE_FAVS).inc()
            _, username = query_clean.split(":", 1)
            results, next_offset = await self._favs_query_results(event.builder, username, offset)
        else:
            gallery_query = self._parse_folder_and_username(query_clean)
            if gallery_query:
                self.usage_counter.labels(use_case=self.USE_CASE_GALLERY).inc()
                folder, username = gallery_query
                results, next_offset = await self._gallery_query_results(event.builder, folder, username, offset)
            else:
                self.usage_counter.labels(use_case=self.USE_CASE_SEARCH).inc()
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

    async def _favs_query_results(
            self,
            builder: InlineBuilder,
            username: str,
            offset: str
    ) -> Tuple[
        List[Coroutine[None, None, Union[InputBotInlineResultPhoto, InputBotInlineResult]]],
        Optional[str]
    ]:
        # For fav listings, the offset can be the last ID
        if offset == "":
            offset = None
        try:
            submissions = (await self.api.get_user_favs(username, offset))[:self.INLINE_MAX]
        except PageNotFound:
            logger.warning("User not found for inline favourites query")
            return self._user_not_found(builder, username), None
        # If no results, send error
        if len(submissions) == 0:
            if offset is None:
                return self._empty_user_favs(builder, username), None
            return [], None
        next_offset = str(submissions[-1].fav_id)
        if next_offset == offset:
            return [], None
        results = [x.to_inline_query_result(builder) for x in submissions]
        return results, next_offset

    async def _gallery_query_results(
            self,
            builder: InlineBuilder,
            folder: str,
            username: str,
            offset: str
    ) -> Tuple[List[Coroutine[None, None, Union[InputBotInlineResult, InputBotInlineResultPhoto]]], Optional[str]]:
        # Parse offset to page and skip
        page, skip = self._parse_offset(offset)
        # Try and get results
        try:
            results = await self._create_user_folder_results(builder, username, folder, page)
        except PageNotFound:
            logger.warning("User not found for inline gallery query")
            return self._user_not_found(builder, username), ""
        # If no results, send error
        if len(results) == 0:
            if page == 1:
                return self._empty_user_folder(builder, username, folder), None
            return [], None
        # Handle paging of big result lists
        return self._page_results(results, page, skip)

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
            builder: InlineBuilder,
            query: str,
            offset: str
    ) -> Tuple[List[Coroutine[None, None, InputBotInlineResult]], Optional[str]]:
        page, skip = self._parse_offset(offset)
        query_clean = query.strip().lower()
        results = await self._create_inline_search_results(builder, query_clean, page)
        if len(results) == 0:
            if page == 1:
                return self._no_search_results_found(builder, query), None
            return [], None
        return self._page_results(results, page, skip)

    def _page_from_offset(self, offset: str) -> int:
        if offset == "":
            offset = 1
        return int(offset)

    async def _create_user_folder_results(
            self,
            builder: InlineBuilder,
            username: str,
            folder: str,
            page: int
    ) -> List[Coroutine[None, None, InputBotInlineResultPhoto]]:
        return [
            x.to_inline_query_result(builder)
            for x
            in await self.api.get_user_folder(username, folder, page)
        ]

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

    def _parse_folder_and_username(self, query_clean: str) -> Optional[Tuple[str, str]]:
        if query_clean.startswith("gallery:") or query_clean.startswith("scraps:"):
            folder, username = query_clean.split(":", 1)
            return folder, username
        else:
            return None

    def _empty_user_folder(
            self,
            builder: InlineBuilder,
            username: str,
            folder: str
    ) -> List[Coroutine[None, None, InputBotInlineResult]]:
        msg = f"There are no submissions in {folder} for user \"{username}\"."
        return [
            builder.article(
                title=f"Nothing in {folder}.",
                description=msg,
                text=msg,
            )
        ]

    def _empty_user_favs(
            self,
            builder: InlineBuilder,
            username: str
    ) -> List[Coroutine[None, None, InputBotInlineResult]]:
        msg = f"There are no favourites for user \"{username}\"."
        return [
            builder.article(
                title=f"Nothing in favourites.",
                description=msg,
                text=msg,
            )
        ]

    def _no_search_results_found(
            self,
            builder: InlineBuilder,
            query: str
    ) -> List[Coroutine[None, None, InputBotInlineResult]]:
        msg = f"No results for search \"{query}\"."
        return [
            builder.article(
                title="No results found.",
                description=msg,
                text=msg,
            )
        ]

    def _user_not_found(
            self,
            builder: InlineBuilder,
            username: str
    ) -> List[Coroutine[None, None, InputBotInlineResult]]:
        msg = f"FurAffinity user does not exist by the name: \"{username}\"."
        return [
            builder.article(
                title="User does not exist.",
                description=msg,
                text=msg,
            )
        ]
