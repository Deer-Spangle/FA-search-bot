import enum
import logging
import re
from typing import List, Union, Optional, Pattern, Dict

import aiohttp
from prometheus_client import Histogram, Counter
from telethon import TelegramClient
from telethon.tl.custom import InlineBuilder
from telethon.tl.types import InputBotInlineResultPhoto, TypeInputPeer, InputBotInlineMessageID

from fa_search_bot.sites.sendable import InlineSendable
from fa_search_bot.sites.sent_submission import SentSubmission
from fa_search_bot.sites.site_handler import SiteHandler, NotFound, HandlerException
from fa_search_bot.sites.site_link import SiteLink
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.sites.weasyl.sendable import WeasylPost

logger = logging.getLogger(__name__)

api_request_times = Histogram(
    "fasearchbot_wzlhandler_request_time_seconds",
    "Request times of the weasyl API, in seconds",
    labelnames=["endpoint"],
)
api_failures = Counter(
    "fasearchbot_wzlhandler_exceptions_total",
    "Total number of exceptions raised while querying the weasyl API",
    labelnames=["endpoint"],
)


class Endpoint(enum.Enum):
    SUBMISSION = "submission"


class WeasylHandler(SiteHandler):
    LINK_REGEX = re.compile("weasyl.com/~[^/]+/submissions/([0-9]+)", re.I)

    def __init__(self):
        self._session: aiohttp.ClientSession = aiohttp.ClientSession()
        for endpoint in Endpoint:
            api_request_times.labels(endpoint=endpoint.value)
            api_failures.labels(endpoint=endpoint.value)

    @property
    def site_name(self) -> str:
        return "Weasyl"

    @property
    def site_code(self) -> str:
        return "wzl"

    @property
    def link_regex(self) -> Pattern:
        return self.LINK_REGEX

    def find_links_in_str(self, haystack: str) -> List[SiteLink]:
        return [SiteLink(self.site_code, match.group(0)) for match in self.LINK_REGEX.finditer(haystack)]

    async def get_submission_id_from_link(self, link: SiteLink) -> Optional[SubmissionID]:
        # Handle submission page link matches
        sub_match = self.LINK_REGEX.match(link.link)
        if sub_match:
            sub_id = SubmissionID(self.site_code, sub_match.group(1))
            logger.info("weasyl link format: post link: %s", sub_id)
            return sub_id
        return None

    def link_for_submission(self, submission_id: str) -> str:
        return f"https://www.weasyl.com/submission/{submission_id}/"

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
        post_data = await self._get_post_by_id(submission_id)
        sendable = WeasylPost(post_data)
        return await sendable.send_message(client, chat, reply_to=reply_to, prefix=prefix, edit=edit)

    def is_valid_submission_id(self, example: str) -> bool:
        try:
            int(example)
            return True
        except ValueError:
            return False

    async def submission_as_answer(
        self, submission_id: SubmissionID, builder: InlineBuilder
    ) -> InputBotInlineResultPhoto:
        post_data = await self._get_post_by_id(submission_id.submission_id)
        sendable = WeasylPost(post_data)
        return await sendable.to_inline_query_result(builder)

    async def _get_post_by_id(self, submission_id: str) -> Dict:
        url = f"https://www.weasyl.com/api/submissions/{submission_id}/view"
        with api_request_times.labels(endpoint=Endpoint.SUBMISSION.value).time():
            with api_failures.labels(endpoint=Endpoint.SUBMISSION.value).count_exceptions():
                async with self._session.get(url) as resp:
                    post_data = await resp.json()
        if "error" in post_data:
            if post_data["error"].get("name") == "submissionRecordMissing":
                raise NotFound("This weasyl post could not be found")
            logger.error(f"Unknown error from weasyl API: {post_data}")
            raise HandlerException("Unknown error from Weasyl API")
        return post_data

    async def get_search_results(self, query: str, page: int) -> List[InlineSendable]:
        return []  # TODO: Weasyl API doesn't have search, at the moment
