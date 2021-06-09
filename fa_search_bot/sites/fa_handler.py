import logging
import re
from re import Pattern
from typing import List, Optional, Union

from telethon import TelegramClient
from telethon.tl.types import TypeInputPeer, InputBotInlineMessageID

from fa_search_bot.sites.fa_export_api import FAExportAPI
from fa_search_bot.sites.fa_submission import FASubmissionShort
from fa_search_bot.sites.site_handler import SiteHandler, HandlerException

logger = logging.getLogger(__name__)


def _get_image_id_from_submission(submission: FASubmissionShort) -> int:
    image_id = re.split(r"[-.]", submission.thumbnail_url)[-2]
    return int(image_id)


class FAHandler(SiteHandler):
    FA_SUB_LINK = re.compile(r"furaffinity\.net/view/([0-9]+)", re.I)
    FA_DIRECT_LINK = re.compile(
        r"d2?\.(?:facdn|furaffinity)\.net/art/([^/]+)/(?:|stories/|poetry/|music/)([0-9]+)/",
        re.I
    )
    FA_THUMB_LINK = re.compile(r"t2?\.(?:facdn|furaffinity)\.net/([0-9]+)@[0-9]+-[0-9]+\.jpg")
    FA_LINKS = re.compile(f"({FA_SUB_LINK.pattern}|{FA_DIRECT_LINK.pattern}|{FA_THUMB_LINK.pattern})")

    def __init__(self, api: FAExportAPI) -> None:
        self.api = api

    @property
    def link_regex(self) -> Pattern:
        return self.FA_LINKS

    def find_links_in_str(self, haystack: str) -> List[str]:
        return [match[0] for match in self.FA_LINKS.findall(haystack)]

    async def get_submission_id_from_link(self, link: str) -> int:
        # Handle submission page link matches
        sub_match = self.FA_SUB_LINK.match(link)
        if sub_match:
            logger.info("Neaten link: submission link")
            return int(sub_match.group(1))
        # Handle thumbnail link matches
        thumb_match = self.FA_THUMB_LINK.match(link)
        if thumb_match:
            logger.info("Neaten link: thumbnail link")
            return int(thumb_match.group(1))
        # Handle direct file link matches
        direct_match = self.FA_DIRECT_LINK.match(link)
        username = direct_match.group(1)
        image_id = int(direct_match.group(2))
        submission_id = await self._find_submission(username, image_id)
        if not submission_id:
            raise HandlerException(
                f"Could not locate the image by {username} with image id {image_id}."
            )
        logger.info("Neaten link: direct image link")
        return submission_id

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
            test_image_id = _get_image_id_from_submission(submission)
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
            if _get_image_id_from_submission(last_submission) <= image_id:
                return listing
            page += 1

    async def send_submission(
            self,
            submission_id: int,
            client: TelegramClient,
            chat: Union[TypeInputPeer, InputBotInlineMessageID],
            *,
            reply_to: Optional[int] = None,
            edit: bool = False
    ) -> None:
        submission = await self.api.get_full_submission(str(submission_id))
        await submission.send_message(client, chat, reply_to=reply_to, edit=edit)

    async def submission_as_answer(
            self,
            submission_id: Union[int, str],
            builder
    ):
        sub = await self.api.get_full_submission(str(submission_id))
        return sub.to_inline_query_result(builder)

    def is_valid_submission_id(self, example: str) -> bool:
        try:
            int(example)
            return True
        except ValueError:
            return False
