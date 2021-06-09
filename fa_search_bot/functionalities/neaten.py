import logging
import re
from typing import Optional, List

from telethon.events import NewMessage, StopPropagation

from fa_search_bot.sites.fa_export_api import PageNotFound, CloudflareError
from fa_search_bot.sites.fa_submission import CantSendFileType
from fa_search_bot.filters import filter_regex
from fa_search_bot.functionalities.functionalities import BotFunctionality, in_progress_msg
from fa_search_bot.sites.fa_handler import FAHandler
from fa_search_bot.sites.site_handler import HandlerException

usage_logger = logging.getLogger("usage")
logger = logging.getLogger(__name__)


async def _return_error_in_privmsg(event: NewMessage.Event, error_message: str) -> None:
    # Only send an error message in private message
    if event.is_private:
        await event.reply(error_message)


class NeatenFunctionality(BotFunctionality):
    FA_SUB_LINK = re.compile(r"furaffinity\.net/view/([0-9]+)", re.I)
    FA_DIRECT_LINK = re.compile(
        r"d2?\.(?:facdn|furaffinity)\.net/art/([^/]+)/(?:|stories/|poetry/|music/)([0-9]+)/",
        re.I
    )
    FA_THUMB_LINK = re.compile(r"t2?\.(?:facdn|furaffinity)\.net/([0-9]+)@[0-9]+-[0-9]+\.jpg")

    def __init__(self, api):
        self.api = api
        self.handler = FAHandler(api)
        super().__init__(NewMessage(func=lambda e: filter_regex(e, self.handler.link_regex), incoming=True))

    async def call(self, event: NewMessage.Event):
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
                await self._handle_fa_submission_link(event, submission_id)
        raise StopPropagation

    def _find_links_in_message(self, event: NewMessage.Event) -> Optional[List[str]]:
        link_matches = []
        # Get links from text
        message = event.message.text
        # Only use image caption in private chats
        if not event.is_private and event.message.photo:
            message = None
        if message is not None:
            link_matches += self.handler.find_links_in_str(message)
        # Get links from buttons
        if event.message.buttons:
            for button_row in event.message.buttons:
                for button in button_row:
                    if button.url:
                        link_matches += self.handler.find_links_in_str(button.url)
        return link_matches

    async def _get_submission_id_from_link(self, event: NewMessage.Event, link: str) -> Optional[int]:
        try:
            return await self.handler.get_submission_id_from_link(link)
        except HandlerException as e:
            logger.warning("Site handler (%s) raised exception:", self.handler.__class__.__name__, exc_info=e)
            await _return_error_in_privmsg(
                event,
                f"Error finding submission: {e}"
            )
            return None

    async def _handle_fa_submission_link(self, event: NewMessage.Event, submission_id: int):
        logger.info("Found a link, ID: %s", submission_id)
        usage_logger.info("Sending neatened submission")
        try:
            await self.handler.send_submission(submission_id, event.client, event.input_chat, reply_to=event.message.id)
        except CantSendFileType as e:
            logger.warning("Can't send file type. Submission ID: %s", submission_id)
            await _return_error_in_privmsg(event, str(e))
        except PageNotFound:
            logger.warning("Submission invalid or deleted. Submission ID: %s", submission_id)
            await _return_error_in_privmsg(
                event,
                "This doesn't seem to be a valid FA submission: "
                "https://www.furaffinity.net/view/{}/".format(submission_id)
            )
        except CloudflareError:
            logger.warning("Cloudflare error")
            await _return_error_in_privmsg(
                event,
                "Furaffinity returned a cloudflare error, so I cannot neaten links."
            )
