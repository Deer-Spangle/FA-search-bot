import logging
import re
from typing import Coroutine, List, Optional, Tuple, Union

from telethon.events import InlineQuery, StopPropagation
from telethon.tl.types import InputBotInlineResult, InputBotInlineResultPhoto

from fa_search_bot.functionalities.functionalities import (
    BotFunctionality,
    answer_with_error,
)
from fa_search_bot.sites.fa_export_api import FAExportAPI, PageNotFound
from fa_search_bot.utils import gather_ignore_exceptions

logger = logging.getLogger(__name__)


class InlineFavsFunctionality(BotFunctionality):
    INLINE_MAX = 20
    USE_CASE_FAVS = "inline_favourites"
    PREFIX_FAVS = ["favourites", "favs", "favorites", "f"]

    def __init__(self, api: FAExportAPI):
        prefix_pattern = re.compile(
            "^(" + "|".join(re.escape(pref) for pref in self.PREFIX_FAVS) + "):", re.I
        )
        super().__init__(InlineQuery(pattern=prefix_pattern))
        self.api = api

    @property
    def usage_labels(self) -> List[str]:
        return [self.USE_CASE_FAVS]

    async def call(self, event: InlineQuery.Event) -> None:
        query_split = event.query.query.split(":", 1)
        offset = event.query.offset
        logger.info("Got an inline favs query, page=%s", offset)
        if len(query_split) != 2 or query_split[0].lower() not in self.PREFIX_FAVS:
            return
        self.usage_counter.labels(function=self.USE_CASE_FAVS).inc()
        username = query_split[1]
        # Get results and next offset
        results, next_offset = await self._favs_query_results(event, username, offset)
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

    async def _favs_query_results(
            self, event: InlineQuery.Event, username: str, offset: Optional[str]
    ) -> Tuple[
        List[
            Coroutine[
                None, None, Union[InputBotInlineResultPhoto, InputBotInlineResult]
            ]
        ],
        Optional[str],
    ]:
        # For fav listings, the offset can be the last ID
        if offset == "":
            offset = None
        try:
            submissions = (await self.api.get_user_favs(username, offset))[
                          : self.INLINE_MAX
                          ]
        except PageNotFound:
            logger.warning("User not found for inline favourites query")
            msg = f'FurAffinity user does not exist by the name: "{username}".'
            await answer_with_error(event, "User does not exist.", msg)
            raise StopPropagation
        # If no results, send error
        if len(submissions) == 0:
            if offset is not None:
                return [], None
            msg = f'There are no favourites for user "{username}".'
            await answer_with_error(event, "Nothing in favourites.", msg)
            raise StopPropagation
        next_offset = str(submissions[-1].fav_id)
        if next_offset == offset:
            return [], None
        results = [x.to_inline_query_result(event.builder) for x in submissions]
        return results, next_offset
