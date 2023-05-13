from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from prometheus_client import Summary
from telethon.events import InlineQuery, StopPropagation

from fa_search_bot.functionalities.functionalities import BotFunctionality, _parse_inline_offset, answer_with_error
from fa_search_bot.sites.furaffinity.fa_export_api import PageNotFound
from fa_search_bot.sites.sent_submission import SentSubmission
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.utils import gather_ignore_exceptions

if TYPE_CHECKING:
    from typing import List, Optional, Tuple

    from telethon.tl.custom import InlineBuilder
    from telethon.tl.types import InputBotInlineResultPhoto

    from fa_search_bot.sites.furaffinity.fa_export_api import FAExportAPI
    from fa_search_bot.sites.furaffinity.fa_submission import FASubmissionShort
    from fa_search_bot.submission_cache import SubmissionCache


logger = logging.getLogger(__name__)

inline_gallery_results = Summary(
    "fasearchbot_inline_gallery_results_count",
    "Number of inline results sent via the inline gallery search",
    labelnames=["source"],
)


class InlineGalleryFunctionality(BotFunctionality):
    INLINE_MAX = 20
    INLINE_FRESH = 5
    USE_CASE_GALLERY = "inline_gallery"
    USE_CASE_SCRAPS = "inline_scraps"
    PREFIX_GALLERY = ["gallery", "g"]
    PREFIX_SCRAPS = ["scraps"]
    ALL_PREFIX = PREFIX_SCRAPS + PREFIX_GALLERY
    LABEL_SOURCE_CACHE = "cache"
    LABEL_SOURCE_FRESH = "fresh"
    LABEL_SOURCE_TOTAL = "total"

    def __init__(self, api: FAExportAPI, submission_cache: SubmissionCache):
        prefix_pattern = re.compile("^(" + "|".join(re.escape(pref) for pref in self.ALL_PREFIX) + "):", re.I)
        super().__init__(InlineQuery(pattern=prefix_pattern))
        self.api = api
        self.cache = submission_cache
        inline_gallery_results.labels(source=self.LABEL_SOURCE_CACHE)
        inline_gallery_results.labels(source=self.LABEL_SOURCE_FRESH)
        inline_gallery_results.labels(source=self.LABEL_SOURCE_TOTAL)

    @property
    def usage_labels(self) -> List[str]:
        return [self.USE_CASE_GALLERY, self.USE_CASE_SCRAPS]

    async def call(self, event: InlineQuery.Event) -> None:
        query_split = event.query.query.split(":", 1)
        offset = event.query.offset
        logger.info("Got an inline query, offset=%s", offset)
        if len(query_split) != 2 or query_split[0].lower() not in self.ALL_PREFIX:
            return
        prefix, username = query_split
        # Determine which folder
        folder = "gallery"
        if prefix in self.PREFIX_SCRAPS:
            folder = "scraps"
            self.usage_counter.labels(function=self.USE_CASE_SCRAPS).inc()
        else:
            self.usage_counter.labels(function=self.USE_CASE_GALLERY).inc()
        # Get results and next offset
        results, next_offset = await self._gallery_query_results(event, folder, username, offset)
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
    ) -> Tuple[List[InputBotInlineResultPhoto], Optional[str]]:
        # Parse offset to page and skip
        page, skip = _parse_inline_offset(offset)
        skip = skip or 0
        # Try and get results
        try:
            results, next_offset = await self._create_user_folder_results(event.builder, username, folder, page, skip)
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
        return results, next_offset

    async def _create_user_folder_results(
            self,
            builder: InlineBuilder,
            username: str,
            folder: str,
            page: int,
            offset: int,
    ) -> Tuple[List[InputBotInlineResultPhoto], Optional[str]]:
        # Get list of submissions
        short_submissions = await self.api.get_user_folder(username, folder, page)
        if not short_submissions:
            return [], None
        # Cut at offset
        short_submissions = short_submissions[offset:]
        # Gather a list of new results until we have the max count, or 5 non-cached ones
        result_coros = []
        fresh_results = 0
        while len(result_coros) < self.INLINE_MAX and fresh_results < self.INLINE_FRESH:
            # If none left in page, fetch the next page
            if not short_submissions:
                page += 1
                offset = 0
                short_submissions = await self.api.get_user_folder(username, folder, page)
                # If next page is empty, return from loop
                if not short_submissions:
                    break
            # Pop submission from list and check cache
            submission = short_submissions.pop(0)
            offset += 1
            sub_id = SubmissionID("fa", submission.submission_id)
            cache_entry = self.cache.load_cache(sub_id, allow_inline=True)
            if cache_entry:
                result_coros.append(cache_entry.as_inline_result(builder))
            else:
                result_coros.append(self._send_fresh_result(builder, submission))
                fresh_results += 1
        # Record some metrics
        inline_gallery_results.labels(source=self.LABEL_SOURCE_TOTAL).observe(len(result_coros))
        inline_gallery_results.labels(source=self.LABEL_SOURCE_FRESH).observe(fresh_results)
        inline_gallery_results.labels(source=self.LABEL_SOURCE_CACHE).observe(len(result_coros) - fresh_results)
        # Await all coros to send results and new offset
        return await gather_ignore_exceptions(result_coros), f"{page}:{offset}"

    async def _send_fresh_result(
            self,
            builder: InlineBuilder,
            submission: FASubmissionShort
    ) -> InputBotInlineResultPhoto:
        sub_id = SubmissionID("fa", submission.submission_id)
        inline_photo = await submission.to_inline_query_result(builder, sub_id.site_code)
        # Save to cache
        sent_sub = SentSubmission.from_inline_result(sub_id, inline_photo)
        self.cache.save_cache(sent_sub)
        return inline_photo
