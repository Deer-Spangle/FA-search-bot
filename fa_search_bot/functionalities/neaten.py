import logging
import re
from typing import Optional, List

from telethon.events import NewMessage, StopPropagation

from fa_search_bot.fa_export_api import PageNotFound, CloudflareError
from fa_search_bot.fa_submission import FASubmissionFull, CantSendFileType, FASubmissionShort
from fa_search_bot.filters import filter_regex
from fa_search_bot.functionalities.functionalities import BotFunctionality, in_progress_msg

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
    FA_LINKS = re.compile(f"({FA_SUB_LINK.pattern}|{FA_DIRECT_LINK.pattern}|{FA_THUMB_LINK.pattern})")

    def __init__(self, api):
        super().__init__(NewMessage(func=lambda e: filter_regex(e, self.FA_LINKS), incoming=True))
        self.api = api

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
            link_matches += [match[0] for match in self.FA_LINKS.findall(message)]
        # Get links from buttons
        if event.message.buttons:
            for button_row in event.message.buttons:
                for button in button_row:
                    button_matches = self.FA_LINKS.findall(button.url)
                    if button_matches:
                        link_matches += [match[0] for match in button_matches]
        return link_matches

    async def _get_submission_id_from_link(self, event: NewMessage.Event, link: str) -> Optional[int]:
        # Handle submission page link matches
        sub_match = self.FA_SUB_LINK.match(link)
        if sub_match:
            usage_logger.info("Neaten link: submission link")
            return int(sub_match.group(1))
        # Handle thumbnail link matches
        thumb_match = self.FA_THUMB_LINK.match(link)
        if thumb_match:
            usage_logger.info("Neaten link: thumbnail link")
            return int(thumb_match.group(1))
        # Handle direct file link matches
        direct_match = self.FA_DIRECT_LINK.match(link)
        username = direct_match.group(1)
        image_id = int(direct_match.group(2))
        submission_id = await self._find_submission(username, image_id)
        if not submission_id:
            logger.warning("Couldn't find submission by username: %s with image id: %s", username, image_id)
            await _return_error_in_privmsg(
                event,
                f"Could not locate the image by {username} with image id {image_id}."
            )
        usage_logger.info("Neaten link: direct image link")
        return submission_id

    async def _handle_fa_submission_link(self, event: NewMessage.Event, submission_id: int):
        logger.info("Found a link, ID: %s", submission_id)
        try:
            submission = await self.api.get_full_submission(str(submission_id))
            await self._send_neat_fa_response(event, submission)
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

    async def _send_neat_fa_response(self, event: NewMessage.Event, submission: FASubmissionFull):
        try:
            await submission.send_message(event.client, event.input_chat, reply_to=event.message.id)
        except CantSendFileType as e:
            await _return_error_in_privmsg(event, str(e))

    async def _find_submission(self, username: str, image_id: int) -> Optional[int]:
        folders = ["gallery", "scraps"]
        for folder in folders:
            submission_id = await self._find_submission_in_folder(username, image_id, folder)
            if submission_id:
                return submission_id
        return None

    async def _find_submission_in_folder(self, username: str, image_id: int, folder: str) -> Optional[int]:
        page_listing = await self._find_correct_page(username, image_id, folder)
        if not page_listing:
            # No page is valid.
            return None
        return self._find_submission_on_page(image_id, page_listing)

    def _find_submission_on_page(self, image_id: int, page_listing: List[FASubmissionShort]) -> Optional[int]:
        for submission in page_listing:
            test_image_id = self._get_image_id_from_submission(submission)
            if image_id == test_image_id:
                return int(submission.submission_id)
            if test_image_id < image_id:
                return None
        return None

    async def _find_correct_page(self, username: str, image_id: int, folder: str) -> Optional[List[FASubmissionShort]]:
        page = 1
        while True:
            listing = await self.api.get_user_folder(username, folder, page)
            if len(listing) == 0:
                return None
            last_submission = listing[-1]
            if self._get_image_id_from_submission(last_submission) <= image_id:
                return listing
            page += 1

    def _get_image_id_from_submission(self, submission: FASubmissionShort) -> int:
        image_id = re.split(r"[-.]", submission.thumbnail_url)[-2]
        return int(image_id)
