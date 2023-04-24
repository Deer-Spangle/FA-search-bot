from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from telethon.events import NewMessage, StopPropagation

from fa_search_bot.filters import filter_regex
from fa_search_bot.functionalities.functionalities import BotFunctionality, in_progress_msg
from fa_search_bot.sites.furaffinity.fa_export_api import CloudflareError, PageNotFound
from fa_search_bot.sites.sendable import CantSendFileType

if TYPE_CHECKING:
    from typing import List, Optional

    from fa_search_bot.sites.handler_group import HandlerGroup
    from fa_search_bot.sites.site_link import SiteLink
    from fa_search_bot.sites.submission_id import SubmissionID

logger = logging.getLogger(__name__)


async def _return_error_in_privmsg(event: NewMessage.Event, error_message: str) -> None:
    # Only send an error message in private message
    if event.is_private:
        await event.reply(error_message)


class NeatenFunctionality(BotFunctionality):
    def __init__(self, handler_group: HandlerGroup):
        self.handlers = handler_group
        link_regex = re.compile(
            "(" + "|".join(handler.link_regex.pattern for handler in handler_group.handlers.values()) + ")",
            re.IGNORECASE,
        )
        super().__init__(NewMessage(func=lambda e: filter_regex(e, link_regex), incoming=True))

    @property
    def usage_labels(self) -> List[str]:
        return [f"neaten_{site_code}" for site_code in self.handlers.site_codes()]

    async def call(self, event: NewMessage.Event) -> None:
        # Only deal with messages, not channel posts
        if event.is_channel and not event.is_group:
            return
        # Get links from message
        links = self._find_links_in_event(event)
        if not links:
            return
        async with in_progress_msg(event, "Neatening image link"):
            logger.info("Neatening links")
            submission_ids = await self.handlers.get_sub_ids_from_links(links)
            if not submission_ids:
                await _return_error_in_privmsg(
                    event,
                    f"Could not find submissions from links: {', '.join(link.link for link in links)}"
                )
                raise StopPropagation
            # Remove duplicates, preserving order
            submission_ids = list(dict.fromkeys(submission_ids))
            # Handle each submission
            for submission_id in submission_ids:
                await self._handle_submission_link(event, submission_id)
        raise StopPropagation

    def _find_links_in_event(self, event: NewMessage.Event) -> Optional[List[SiteLink]]:
        link_matches: List[SiteLink] = []
        # Get links from text
        message = event.message.text
        # Only use image caption in private chats
        if (event.message.document or event.message.photo) and not event.is_private:
            message = None
        # Find links in text
        if message is not None:
            link_matches += self.handlers.list_potential_links(message)
        # Get links from buttons
        if event.message.buttons:
            for button_row in event.message.buttons:
                for button in button_row:
                    if button.url:
                        link_matches += self.handlers.list_potential_links(button.url)
        return link_matches

    async def _handle_submission_link(self, event: NewMessage.Event, sub_id: SubmissionID) -> None:
        logger.info("Found a link, ID: %s", sub_id)
        self.usage_counter.labels(function=f"neaten_{sub_id.site_code}").inc()
        try:
            await self.handlers.send_submission(sub_id, event)
        except CantSendFileType as e:
            logger.warning("Can't send file type. Submission ID: %s", sub_id)
            await _return_error_in_privmsg(event, str(e))
        except PageNotFound:
            logger.warning("Submission invalid or deleted. Submission ID: %s", sub_id)
            handler = self.handlers.handler_for_sub_id(sub_id)
            if handler:
                await _return_error_in_privmsg(
                    event,
                    f"This doesn't seem to be a valid {handler.site_name} submission: "
                    f"{handler.link_for_submission(sub_id.submission_id)}",
                )
            else:
                await _return_error_in_privmsg(
                    event,
                    f"This doesn't seem to be a valid submission, no site could be found for submission ID: {sub_id}"
                )
        except CloudflareError:
            logger.warning("Cloudflare error")
            site_name = "The site"
            handler = self.handlers.handler_for_sub_id(sub_id)
            if handler:
                site_name = handler.site_name
            await _return_error_in_privmsg(
                event,
                f"{site_name} returned a cloudflare error, so I cannot neaten links.",
            )
        except Exception as e:
            logger.error("Unhandled exception trying to neaten submission %s", sub_id, exc_info=e)
            raise e
