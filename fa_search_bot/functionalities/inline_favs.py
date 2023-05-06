from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from prometheus_client import Summary
from telethon.events import InlineQuery, StopPropagation

from fa_search_bot.functionalities.functionalities import BotFunctionality, answer_with_error
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

inline_fav_results = Summary(
    "fasearchbot_inline_favs_results_count",
    "Number of inline results sent via the inline favourites search",
    labelnames=["source"],
)


class InlineFavsFunctionality(BotFunctionality):
    INLINE_MAX = 20
    INLINE_FRESH = 5
    USE_CASE_FAVS = "inline_favourites"
    PREFIX_FAVS = ["favourites", "favs", "favorites", "f"]
    LABEL_SOURCE_CACHE = "cache"
    LABEL_SOURCE_FRESH = "fresh"
    LABEL_SOURCE_TOTAL = "total"

    def __init__(self, api: FAExportAPI, submission_cache: SubmissionCache):
        prefix_pattern = re.compile("^(" + "|".join(re.escape(pref) for pref in self.PREFIX_FAVS) + "):", re.I)
        super().__init__(InlineQuery(pattern=prefix_pattern))
        self.api = api
        self.cache = submission_cache
        inline_fav_results.labels(source=self.LABEL_SOURCE_CACHE)
        inline_fav_results.labels(source=self.LABEL_SOURCE_FRESH)
        inline_fav_results.labels(source=self.LABEL_SOURCE_TOTAL)

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
        # For fav listings, the offset can be the last fav ID
        if offset == "":
            offset = None
        # Fetch list of favs
        try:
            fav_submissions = await self.api.get_user_favs(username, offset)
        except PageNotFound:
            logger.warning("User not found for inline favourites query")
            msg = f'FurAffinity user does not exist by the name: "{username}".'
            await answer_with_error(event, "User does not exist.", msg)
            raise StopPropagation
        # If no results, send error or end results list
        if len(fav_submissions) == 0:
            if offset is not None:
                return [], None
            msg = f'There are no favourites for user "{username}".'
            await answer_with_error(event, "Nothing in favourites.", msg)
            raise StopPropagation
        # If last offset in results is equal to previous offset, it's the end of the list
        if str(fav_submissions[-1].fav_id) == offset:
            return [], None
        # Generate results
        results = []
        fresh_results = 0
        next_offset = None
        while len(results) < self.INLINE_MAX and fresh_results < self.INLINE_FRESH:
            submission = fav_submissions.pop(0)
            next_offset = str(submission.fav_id)
            sub_id = SubmissionID("fa", submission.submission_id)
            cache_entry = self.cache.load_cache(sub_id, allow_inline=True)
            if cache_entry:
                results.append(cache_entry.as_inline_result(event.builder))
            else:
                fresh_results += 1
                results.append(self._send_fresh_result(submission, event.builder))
        # Record some metrics
        inline_fav_results.labels(source=self.LABEL_SOURCE_TOTAL).observe(len(results))
        inline_fav_results.labels(source=self.LABEL_SOURCE_FRESH).observe(fresh_results)
        inline_fav_results.labels(source=self.LABEL_SOURCE_CACHE).observe(len(results) - fresh_results)
        # Await all the coros and return them and the new offset
        return await gather_ignore_exceptions(results), next_offset

    async def _send_fresh_result(
            self,
            submission: FASubmissionShortFav,
            builder: InlineBuilder,
    ) -> InputBotInlineResultPhoto:
        sub_id = SubmissionID("fa", submission.submission_id)
        # Send from source
        result = await submission.to_inline_query_result(builder, sub_id.site_code)
        # Save to cache
        sent_sub = SentSubmission.from_inline_result(sub_id, result)
        self.cache.save_cache(sent_sub)
        return result
