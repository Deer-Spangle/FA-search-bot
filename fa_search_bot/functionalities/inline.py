import asyncio
import logging
from typing import Tuple, List, Union, Optional, Coroutine

from telethon.events import InlineQuery, StopPropagation
from telethon.tl.custom import InlineBuilder
from telethon.tl.types import InputBotInlineResultPhoto, InputBotInlineResult

from fa_search_bot.fa_export_api import FAExportAPI, PageNotFound
from fa_search_bot.functionalities.functionalities import BotFunctionality

usage_logger = logging.getLogger("usage")
logger = logging.getLogger(__name__)


class InlineFunctionality(BotFunctionality):

    def __init__(self, api: FAExportAPI):
        super().__init__(InlineQuery())
        self.api = api

    async def call(self, event: InlineQuery.Event):
        query = event.query.query
        query_clean = query.strip().lower()
        offset = event.query.offset
        logger.info("Got an inline query, page=%s", offset)
        if query_clean == "":
            await event.answer([])
            return
        # Get results and next offset
        if any(query_clean.startswith(x) for x in ["favourites:", "favs:", "favorites:"]):
            usage_logger.info("Inline favourites")
            _, username = query_clean.split(":", 1)
            results, next_offset = self._favs_query_results(event.builder, username, offset)
        else:
            gallery_query = self._parse_folder_and_username(query_clean)
            if gallery_query:
                usage_logger.info("Inline gallery")
                folder, username = gallery_query
                results, next_offset = self._gallery_query_results(event.builder, folder, username, offset)
            else:
                usage_logger.info("Inline search")
                results, next_offset = self._search_query_results(event.builder, query, offset)
        # Await results while ignoring exceptions
        results = list(filter(
            lambda x: not isinstance(x, Exception),
            await asyncio.gather(*results, return_exceptions=True)
        ))
        logger.info(f"There are {len(results)} results.")
        # Send results
        await event.answer(
            results,
            next_offset=str(next_offset) if next_offset else None
        )
        raise StopPropagation

    def _favs_query_results(
            self,
            builder: InlineBuilder,
            username: str,
            offset: str
    ) -> Tuple[List[Coroutine[None, None, Union[InputBotInlineResultPhoto, InputBotInlineResult]]], Union[int, str]]:
        if offset == "":
            offset = None
        try:
            submissions = self.api.get_user_favs(username, offset)[:48]
        except PageNotFound:
            logger.warning("User not found for inline favourites query")
            return self._user_not_found(builder, username), ""
        # If no results, send error
        if len(submissions) > 0:
            next_offset = submissions[-1].fav_id
            if next_offset == offset:
                submissions = []
                next_offset = ""
        else:
            next_offset = ""
            if offset is None:
                return self._empty_user_favs(builder, username), ""
        results = [x.to_inline_query_result(builder) for x in submissions]
        return results, next_offset

    def _gallery_query_results(
            self,
            builder: InlineBuilder,
            folder: str,
            username: str,
            offset: str
    ) -> Tuple[List[Coroutine[None, None, Union[InputBotInlineResult, InputBotInlineResultPhoto]]], Union[int, str]]:
        # Parse offset to page and skip
        if offset == "":
            page, skip = 1, None
        elif ":" in offset:
            page, skip = (int(x) for x in offset.split(":", 1))
        else:
            page, skip = int(offset), None
        # Default next offset
        next_offset = page + 1
        # Try and get results
        try:
            results = self._create_user_folder_results(builder, username, folder, page)
        except PageNotFound:
            logger.warning("User not found for inline gallery query")
            return self._user_not_found(builder, username), ""
        # If no results, send error
        if len(results) == 0:
            next_offset = ""
            if page == 1:
                return self._empty_user_folder(builder, username, folder), ""
        # Handle paging of big result lists
        if skip:
            results = results[skip:]
        if len(results) > 48:
            results = results[:48]
            if skip:
                skip += 48
            else:
                skip = 48
            next_offset = f"{page}:{skip}"
        return results, next_offset

    def _search_query_results(
            self,
            builder: InlineBuilder,
            query: str,
            offset: str
    ) -> Tuple[List[Coroutine[None, None, InputBotInlineResult]], Union[int, str]]:
        page = self._page_from_offset(offset)
        query_clean = query.strip().lower()
        next_offset = page + 1
        results = self._create_inline_search_results(builder, query_clean, page)
        if len(results) == 0:
            next_offset = ""
            if page == 1:
                results = self._no_search_results_found(builder, query)
        return results, next_offset

    def _page_from_offset(self, offset: str) -> int:
        if offset == "":
            offset = 1
        return int(offset)

    def _create_user_folder_results(
            self,
            builder: InlineBuilder,
            username: str,
            folder: str,
            page: int
    ) -> List[Coroutine[None, None, InputBotInlineResultPhoto]]:
        return [
            x.to_inline_query_result(builder)
            for x
            in self.api.get_user_folder(username, folder, page)
        ]

    def _create_inline_search_results(
            self,
            builder: InlineBuilder,
            query_clean: str,
            page: int
    ) -> List[Coroutine[None, None, InputBotInlineResultPhoto]]:
        return [
            x.to_inline_query_result(builder)
            for x
            in self.api.get_search_results(query_clean, page)
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
                text=msg
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
