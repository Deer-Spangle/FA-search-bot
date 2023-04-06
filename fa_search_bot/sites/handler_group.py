from typing import List

from telethon.events import InlineQuery
from telethon.tl.types import InputBotInlineResultPhoto

from fa_search_bot.sites.site_handler import SiteHandler
from fa_search_bot.sites.site_link import SiteLink
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.utils import gather_ignore_exceptions


class HandlerGroup:
    def __init__(self, handlers: List[SiteHandler]) -> None:
        super().__init__()
        self.handlers = {
            handler.site_code: handler for handler in handlers
        }

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

    def site_codes(self) -> List[str]:
        return [h.site_code for h in self.handlers.values()]

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
