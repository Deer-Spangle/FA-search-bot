from __future__ import annotations
import logging
from typing import List, Optional, Dict, TYPE_CHECKING


from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.utils import gather_ignore_exceptions
from fa_search_bot.sites.sent_submission import SentSubmission
from fa_search_bot.sites.site_handler import SiteHandler, NotFound

if TYPE_CHECKING:
    from telethon import TelegramClient
    from telethon.events import InlineQuery, NewMessage
    from telethon.tl.custom import InlineBuilder
    from telethon.tl.types import InputBotInlineResultPhoto, InputBotInlineMessageID

    from fa_search_bot.sites.sendable import InlineSendable
    from fa_search_bot.sites.site_link import SiteLink
    from fa_search_bot.submission_cache import SubmissionCache

logger = logging.getLogger(__name__)


class HandlerGroup:
    def __init__(self, handlers: List[SiteHandler], submission_cache: SubmissionCache) -> None:
        super().__init__()
        self.handlers: Dict[str, SiteHandler] = {handler.site_code: handler for handler in handlers}
        self.default = handlers[0]
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

    def list_potential_filenames(self, query: str) -> List[SiteLink]:
        filenames = []
        for handler in self.handlers.values():
            filenames += handler.find_filenames_in_str(query)
        return filenames

    async def get_sub_ids_from_links(self, links: List[SiteLink]) -> List[SubmissionID]:
        return [sub_id for sub_id in await gather_ignore_exceptions([
            self.handlers[link.site_code].get_submission_id_from_link(link)
            for link in links
            if link.site_code in self.handlers
        ]) if sub_id is not None]

    async def get_sub_ids_from_filenames(self, filenames: List[SiteLink]) -> List[SubmissionID]:
        return [sub_id for sub_id in await gather_ignore_exceptions([
            self.handlers[filename.site_code].get_submission_id_from_filename(filename)
            for filename in filenames
            if filename.site_code in self.handlers
        ])]

    async def answer_submission(self, sub_id: SubmissionID, event: InlineQuery.Event) -> InputBotInlineResultPhoto:
        cache_entry = self.cache.load_cache(sub_id, allow_inline=True)
        if cache_entry:
            return await cache_entry.as_inline_result(event.builder)
        handler = self.handlers.get(sub_id.site_code)
        if not handler:
            raise NotFound(f"Handler not found matching site code: {sub_id.site_code}")
        # Send from source
        inline_photo = await handler.submission_as_answer(sub_id, event.builder)
        # Save to cache
        sent_sub = SentSubmission.from_inline_result(sub_id, inline_photo)
        self.cache.save_cache(sent_sub)
        return inline_photo

    async def answer_submission_ids(
            self,
            sub_ids: List[SubmissionID],
            event: InlineQuery.Event
    ) -> List[InputBotInlineResultPhoto]:
        return await gather_ignore_exceptions([self.answer_submission(sub_id, event) for sub_id in sub_ids])

    async def answer_link(self, link: SiteLink, event: InlineQuery.Event) -> InputBotInlineResultPhoto:
        handler = self.handlers.get(link.site_code)
        if not handler:
            raise NotFound(f"Handler not found matching site code: {link.site_code}")
        sub_id = await handler.get_submission_id_from_link(link)
        if sub_id is None:
            raise NotFound(f"Could not find submission ID for link: {link.link}")
        # Check cache
        cache_entry = self.cache.load_cache(sub_id, allow_inline=True)
        if cache_entry:
            return await cache_entry.as_inline_result(event.builder)
        # Send from source
        inline_photo = await handler.submission_as_answer(sub_id, event.builder)
        # Save to cache
        sent_sub = SentSubmission.from_inline_result(sub_id, inline_photo)
        self.cache.save_cache(sent_sub)
        return inline_photo

    async def answer_links(self, links: List[SiteLink], event: InlineQuery.Event) -> List[InputBotInlineResultPhoto]:
        return await gather_ignore_exceptions([self.answer_link(link, event) for link in links])

    async def search(self, query: str, page: int) -> List[InlineSendable]:
        search_handler = self.default
        if ":" in query:
            prefix, query = query.split(":", 1)
            prefix_clean = prefix.strip().lower()
            for handler in self.handlers.values():
                if prefix_clean in handler.search_prefixes:
                    search_handler = handler
                    break
        return await search_handler.get_search_results(query.strip(), page)

    async def answer_search(self, query: str, event: InlineQuery.Event, page: int) -> List[InputBotInlineResultPhoto]:
        results = await self.search(query, page)
        return await gather_ignore_exceptions([
            self._answer_inline_sendable(result, event.builder) for result in results
        ])

    async def _answer_inline_sendable(
            self,
            sendable: InlineSendable,
            builder: InlineBuilder
    ) -> InputBotInlineResultPhoto:
        cache_entry = self.cache.load_cache(sendable.submission_id, allow_inline=True)
        if cache_entry:
            return await cache_entry.as_inline_result(builder)
        # Send from source
        inline_photo = await sendable.to_inline_query_result(builder)
        # Save to cache
        sent_sub = SentSubmission.from_inline_result(sendable.submission_id, inline_photo)
        self.cache.save_cache(sent_sub)
        # Can't save cache of inline sendable, unfortunately
        return inline_photo

    async def send_submission(self, sub_id: SubmissionID, reply_to: NewMessage.Event) -> SentSubmission:
        handler = self.handlers.get(sub_id.site_code)
        if handler is None:
            logger.error("Unrecognised site code (%s) trying to send submission: %s")
            raise NotFound(f"Handler not found matching site code: {sub_id.site_code}")
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

    async def edit_submission(
            self,
            sub_id: SubmissionID,
            client: TelegramClient,
            msg_id: InputBotInlineMessageID,
    ) -> SentSubmission:
        handler = self.handlers.get(sub_id.site_code)
        if handler is None:
            logger.error("Unrecognised site code (%s) trying to edit submission: %s")
            raise NotFound(f"Handler not found matching site code: {sub_id.site_code}")
        cache_entry = self.cache.load_cache(sub_id)
        if cache_entry:
            if await cache_entry.try_to_edit(client, msg_id):
                return cache_entry
        sent_sub = await handler.send_submission(
            sub_id.submission_id,
            client,
            msg_id,
            edit=True,
        )
        self.cache.save_cache(sent_sub)
        return sent_sub
