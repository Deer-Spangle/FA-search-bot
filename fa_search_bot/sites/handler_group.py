import logging
from typing import List, Optional

from telethon.events import InlineQuery, NewMessage
from telethon.tl.types import InputBotInlineResultPhoto

from fa_search_bot.sites.furaffinity.fa_export_api import PageNotFound
from fa_search_bot.sites.sent_submission import SentSubmission
from fa_search_bot.sites.site_handler import SiteHandler
from fa_search_bot.sites.site_link import SiteLink
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.submission_cache import SubmissionCache
from fa_search_bot.utils import gather_ignore_exceptions

logger = logging.getLogger(__name__)


class HandlerGroup:
    def __init__(self, handlers: List[SiteHandler], submission_cache: SubmissionCache) -> None:
        super().__init__()
        self.handlers = {
            handler.site_code: handler for handler in handlers
        }
        self.cache = submission_cache

    def site_codes(self) -> List[str]:
        return [h.site_code for h in self.handlers.values()]

    def handler_for_sub_id(self, sub_id: SubmissionID) -> Optional[SiteHandler]:
        return self.handlers.get(sub_id.site_code)

    def list_potential_submission_ids(self, query: str) -> List[SubmissionID]:
        return [
            SubmissionID(handler.site_code, query)
            for handler in self.handlers.values()
            if handler.is_valid_submission_id(query)
        ]

    def list_potential_links(self, query: str) -> List[SiteLink]:
        links = []
        for handler in self.handlers.values():
            links += handler.find_links_in_str(query)
        return links

    async def get_sub_ids_from_links(self, links: List[SiteLink]) -> List[SubmissionID]:
        return await gather_ignore_exceptions([
            self.handlers[link.site_code].get_submission_id_from_link(link)
            for link in links
            if link.site_code in self.handlers
        ])

    async def answer_submission_ids(self, sub_ids: List[SubmissionID], event: InlineQuery.Event) -> List[InputBotInlineResultPhoto]:
        return await gather_ignore_exceptions([
            self.handlers[sub_id.site_code].submission_as_answer(sub_id, event.builder)
            for sub_id in sub_ids
            if sub_id.site_code in self.handlers
        ])

    async def answer_links(self, links: List[SiteLink], event: InlineQuery.Event) -> List[InputBotInlineResultPhoto]:
        results = await gather_ignore_exceptions([
            self.handlers[link.site_code].link_as_answer(link, event.builder)
            for link in links
            if link.site_code in self.handlers
        ])
        return [result for result in results if result is not None]

    async def send_submission(self, sub_id: SubmissionID, reply_to: NewMessage.Event) -> SentSubmission:
        handler = self.handlers.get(sub_id.site_code)
        if handler is None:
            logger.error("Unrecognised site code (%s) trying to send submission: %s")
            raise PageNotFound(f"Handler not found matching site code: {sub_id.site_code}")
        cache_entry = self.cache.load_cache(sub_id)
        if cache_entry:
            if await cache_entry.try_to_reply(reply_to):
                return cache_entry
        sent_sub = await handler.send_submission(
            sub_id.submission_id,
            reply_to.client,
            reply_to.input_chat,
            reply_to=reply_to.message.id,
        )
        self.cache.save_cache(sent_sub)
        return sent_sub
