from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from telethon.events import NewMessage, StopPropagation

from fa_search_bot.filters import filter_regex
from fa_search_bot.functionalities.functionalities import BotFunctionality, in_progress_msg
from fa_search_bot.sites.furaffinity.fa_export_api import CloudflareError, PageNotFound
from fa_search_bot.sites.sendable import CantSendFileType
from fa_search_bot.sites.site_handler import HandlerException, SubmissionID

if TYPE_CHECKING:
    from typing import Dict, List, Optional

    from fa_search_bot.sites.site_handler import SiteHandler
    from fa_search_bot.submission_cache import SubmissionCache

logger = logging.getLogger(__name__)


async def _return_error_in_privmsg(event: NewMessage.Event, error_message: str) -> None:
    # Only send an error message in private message
    if event.is_private:
        await event.reply(error_message)


class NeatenFunctionality(BotFunctionality):
    def __init__(self, handlers: Dict[str, SiteHandler], submission_cache: SubmissionCache):
        self.handlers = handlers
        self.cache = submission_cache
        link_regex = re.compile(
            "(" + "|".join(handler.link_regex.pattern for handler in handlers.values()) + ")",
            re.IGNORECASE,
        )
        super().__init__(NewMessage(func=lambda e: filter_regex(e, link_regex), incoming=True))

    @property
    def usage_labels(self) -> List[str]:
        return [f"neaten_{handler.site_code}" for handler in self.handlers.values()]

    async def call(self, event: NewMessage.Event) -> None:
        # Only deal with messages, not channel posts
        if event.is_channel and not event.is_group:
            return
        # Get links from message
        matches = self._find_links_in_message(event)
        if not matches:
            return
        submission_ids = []
        async with in_progress_msg(event, "Neatening image link"):
            logger.info("Neatening links")
            for match in matches:
                submission_id = await self._get_submission_id_from_link(event, match)
                if submission_id:
                    submission_ids.append(submission_id)
            # Remove duplicates, preserving order
            submission_ids = list(dict.fromkeys(submission_ids))
            # Handle each submission
            for submission_id in submission_ids:
                await self._handle_submission_link(event, submission_id)
        raise StopPropagation

    def _find_links_in_message(self, event: NewMessage.Event) -> Optional[List[str]]:
        link_matches = []
        # Get links from text
        message = event.message.text
        # Only use image caption in private chats
        if (event.message.document or event.message.photo) and not event.is_private:
            message = None
        if message is not None:
            for handler in self.handlers.values():
                link_matches += handler.find_links_in_str(message)
        # Get links from buttons
        if event.message.buttons:
            for button_row in event.message.buttons:
                for button in button_row:
                    if button.url:
                        for handler in self.handlers.values():
                            link_matches += handler.find_links_in_str(button.url)
        return link_matches

    async def _get_submission_id_from_link(self, event: NewMessage.Event, link: str) -> Optional[SubmissionID]:
        for site_code, handler in self.handlers.items():
            try:
                sub_id = await handler.get_submission_id_from_link(link)
                if sub_id is not None:
                    return SubmissionID(site_code, sub_id)
            except HandlerException as e:
                logger.warning(
                    "Site handler (%s) raised exception:",
                    handler.__class__.__name__,
                    exc_info=e,
                )
                await _return_error_in_privmsg(event, f"Error finding submission: {e}")
                return None
        return None

    async def _handle_submission_link(self, event: NewMessage.Event, sub_id: SubmissionID) -> None:
        logger.info("Found a link, ID: %s", sub_id)
        self.usage_counter.labels(function=f"neaten_{sub_id.site_code}").inc()
        handler = self.handlers.get(sub_id.site_code)
        if handler is None:
            return
        cache_entry = self.cache.load_cache(sub_id)
        if cache_entry:
            if await cache_entry.try_to_reply(event):
                return
        try:
            sent_sub = await handler.send_submission(
                sub_id.submission_id,
                event.client,
                event.input_chat,
                reply_to=event.message.id,
            )
        except CantSendFileType as e:
            logger.warning("Can't send file type. Submission ID: %s", sub_id)
            await _return_error_in_privmsg(event, str(e))
        except PageNotFound:
            logger.warning("Submission invalid or deleted. Submission ID: %s", sub_id)
            await _return_error_in_privmsg(
                event,
                f"This doesn't seem to be a valid {handler.site_name} submission: "
                f"{handler.link_for_submission(sub_id.submission_id)}",
            )
        except CloudflareError:
            logger.warning("Cloudflare error")
            await _return_error_in_privmsg(
                event,
                f"{handler.site_name} returned a cloudflare error, so I cannot neaten links.",
            )
        else:
            self.cache.save_cache(sent_sub)
