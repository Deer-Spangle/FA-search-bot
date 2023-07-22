from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from fa_search_bot.sites.furaffinity.fa_export_api import FAExportAPI, PageNotFound
from fa_search_bot.sites.furaffinity.sendable import SendableFASubmission, InlineSendableFASubmission
from fa_search_bot.sites.site_handler import HandlerException, SiteHandler, NotFound
from fa_search_bot.sites.site_link import SiteLink
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.utils import regex_combine

if TYPE_CHECKING:
    from re import Pattern
    from typing import List, Optional, Union

    from telethon import TelegramClient
    from telethon.tl.custom import InlineBuilder
    from telethon.tl.types import InputBotInlineMessageID, InputBotInlineResultPhoto, TypeInputPeer

    from fa_search_bot.sites.furaffinity.fa_submission import FASubmissionShort
    from fa_search_bot.sites.sendable import InlineSendable
    from fa_search_bot.sites.sent_submission import SentSubmission

logger = logging.getLogger(__name__)


def _get_image_id_from_submission(submission: FASubmissionShort) -> int:
    image_id = re.split(r"[-.]", submission.thumbnail_url)[-2]
    return int(image_id)


class FAHandler(SiteHandler):
    FA_SUB_LINK = re.compile(r"furaffinity\.net/view/([0-9]+)", re.I)
    FA_DIRECT_LINK = re.compile(
        r"d2?\.(?:facdn|furaffinity)\.net/art/([^/]+)/(?:|stories/|poetry/|music/)([0-9]+)/([0-9]+)\S+",
        re.I,
    )
    FA_THUMB_LINK = re.compile(r"t2?\.(?:facdn|furaffinity)\.net/([0-9]+)@[0-9]+-[0-9]+\.jpg", re.I)
    FA_LINKS = regex_combine(FA_SUB_LINK, FA_DIRECT_LINK, FA_THUMB_LINK)
    FA_FILES = re.compile(r"([0-9]+)\.([^_]+)_\S.gif(\.mp4)?", re.I)

    def __init__(self, api: FAExportAPI) -> None:
        self.api = api

    @property
    def site_name(self) -> str:
        return "Furaffinity"

    @property
    def site_code(self) -> str:
        return "fa"

    @property
    def link_regex(self) -> Pattern:
        return self.FA_LINKS

    @property
    def filename_regex(self) -> Pattern:
        return regex_combine(self.FA_FILES, self._fasearchbot_filename_regex)

    def find_links_in_str(self, haystack: str) -> List[SiteLink]:
        return [SiteLink(self.site_code, match.group(0)) for match in self.link_regex.finditer(haystack)]

    def find_filenames_in_str(self, haystack: str) -> List[SiteLink]:
        return [SiteLink(self.site_code, match.group(0)) for match in self.filename_regex.finditer(haystack)]

    async def get_submission_id_from_link(self, link: SiteLink) -> Optional[SubmissionID]:
        # Handle submission page link matches
        sub_match = self.FA_SUB_LINK.match(link.link)
        if sub_match:
            sub_id = SubmissionID(self.site_code, sub_match.group(1))
            logger.info("FA link: submission link: %s", sub_id)
            return sub_id
        # Handle thumbnail link matches
        thumb_match = self.FA_THUMB_LINK.match(link.link)
        if thumb_match:
            sub_id = SubmissionID(self.site_code, thumb_match.group(1))
            logger.info("FA link: thumbnail link: %s", sub_id)
            return sub_id
        # Handle direct file link matches
        direct_match = self.FA_DIRECT_LINK.match(link.link)
        if not direct_match:
            return None
        username = direct_match.group(1)
        image_id_1 = int(direct_match.group(2))
        image_id_2 = int(direct_match.group(3))
        submission_id = await self._find_submission(username, image_id_1)
        if not submission_id:
            submission_id = await self._find_submission(username, image_id_2)
            if not submission_id:
                raise HandlerException(
                    f"Could not locate the image by {username} with image id {image_id_1} or {image_id_2}."
                )
        sub_id = SubmissionID(self.site_code, submission_id)
        logger.info("FA link: direct image link: %s", sub_id)
        return sub_id

    async def get_submission_id_from_filename(self, filename: SiteLink) -> Optional[SubmissionID]:
        # Handle FASearchBot filenames
        fas_filename = self._fasearchbot_filename_regex.match(filename.link)
        if fas_filename:
            sub_id = SubmissionID(self.site_code, fas_filename.group(1))
            logger.info("FA filename format: FASearchBot filename: %s", sub_id)
            return sub_id
        # Handle FurAffinity filenames
        fa_filename = self.FA_FILES.match(filename.link)
        if fa_filename:
            username = fa_filename.group(2)
            image_id = fa_filename.group(1)
            submission_id = await self._find_submission(username, image_id)
            if submission_id:
                sub_id = SubmissionID(self.site_code, submission_id)
                logger.info("FA filename format: FA direct document link: %s", sub_id)
                return sub_id
        return None

    async def _find_submission(self, username: str, image_id: int) -> Optional[str]:
        folders = ["gallery", "scraps"]
        for folder in folders:
            submission_id = await self._find_submission_in_folder(username, image_id, folder)
            if submission_id:
                return submission_id
        return None

    async def _find_submission_in_folder(self, username: str, image_id: int, folder: str) -> Optional[str]:
        page_listing = await self._find_correct_page(username, image_id, folder)
        if not page_listing:
            # No page is valid.
            return None
        return self._find_submission_on_page(image_id, page_listing)

    def _find_submission_on_page(self, image_id: int, page_listing: List[FASubmissionShort]) -> Optional[str]:
        for submission in page_listing:
            test_image_id = _get_image_id_from_submission(submission)
            if image_id == test_image_id:
                return submission.submission_id
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

    def link_for_submission(self, submission_id: str) -> str:
        return f"https://www.furaffinity.net/view/{submission_id}/"

    async def send_submission(
        self,
        submission_id: str,
        client: TelegramClient,
        chat: Union[TypeInputPeer, InputBotInlineMessageID],
        *,
        reply_to: Optional[int] = None,
        prefix: str = None,
        edit: bool = False,
    ) -> SentSubmission:
        try:
            submission = await self.api.get_full_submission(str(submission_id))
        except PageNotFound as e:
            raise NotFound(e)
        sendable = SendableFASubmission(submission)
        return await sendable.send_message(client, chat, reply_to=reply_to, prefix=prefix, edit=edit)

    async def submission_as_answer(
        self, submission_id: SubmissionID, builder: InlineBuilder
    ) -> InputBotInlineResultPhoto:
        sub = await self.api.get_full_submission(submission_id.submission_id)
        sendable = SendableFASubmission(sub)
        return await sendable.to_inline_query_result(builder)

    def is_valid_submission_id(self, example: str) -> bool:
        try:
            int(example)
            return True
        except ValueError:
            return False

    async def get_search_results(self, query: str, page: int) -> List[InlineSendable]:
        posts = await self.api.get_search_results(query, page)
        return [InlineSendableFASubmission(post) for post in posts]
