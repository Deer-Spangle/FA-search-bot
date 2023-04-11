from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from telethon.events import InlineQuery, StopPropagation

from fa_search_bot.functionalities.functionalities import BotFunctionality, answer_with_error, log_inline_exceptions
from fa_search_bot.sites.furaffinity.fa_export_api import PageNotFound
from fa_search_bot.sites.sent_submission import SentSubmission
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.utils import gather_ignore_exceptions

if TYPE_CHECKING:
    from typing import List, Optional, Tuple

    from telethon.tl.types import InputBotInlineResultPhoto
    from telethon.tl.custom import InlineBuilder

    from fa_search_bot.sites.furaffinity.fa_export_api import FAExportAPI
    from fa_search_bot.sites.furaffinity.fa_submission import FASubmissionShortFav
    from fa_search_bot.submission_cache import SubmissionCache

logger = logging.getLogger(__name__)


class InlineFavsFunctionality(BotFunctionality):
    INLINE_MAX = 20
    USE_CASE_FAVS = "inline_favourites"
    PREFIX_FAVS = ["favourites", "favs", "favorites", "f"]

    def __init__(self, api: FAExportAPI, submission_cache: SubmissionCache):
        prefix_pattern = re.compile("^(" + "|".join(re.escape(pref) for pref in self.PREFIX_FAVS) + "):", re.I)
        super().__init__(InlineQuery(pattern=prefix_pattern))
        self.api = api
        self.cache = submission_cache

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
        with log_inline_exceptions(msg="Failed to list inline favs"):
            # Get results and next offset
            results, next_offset = await self._favs_query_results(event, username, offset)
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
    ) -> Tuple[List[InputBotInlineResultPhoto], Optional[str]]:
        # For fav listings, the offset can be the last ID
        if offset == "":
            offset = None
        try:
            submissions = (await self.api.get_user_favs(username, offset))[: self.INLINE_MAX]
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
        results = await gather_ignore_exceptions(
            [self.inline_query_photo(submission, event.builder) for submission in submissions]
        )
        return results, next_offset

    async def inline_query_photo(
            self, submission: FASubmissionShortFav, builder: InlineBuilder
    ) -> InputBotInlineResultPhoto:
        sub_id = SubmissionID("fa", submission.submission_id)
        cache_entry = self.cache.load_cache(sub_id, allow_inline=True)
        if cache_entry:
            return await cache_entry.as_inline_result(builder)
        # Send from source
        result = await submission.to_inline_query_result(builder)
        # Save to cache
        sent_sub = SentSubmission.from_inline_result(sub_id, result)
        self.cache.save_cache(sent_sub)
        return result
