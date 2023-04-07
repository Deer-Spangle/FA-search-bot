from __future__ import annotations

import enum
import logging
import re
from typing import TYPE_CHECKING

from prometheus_client.metrics import Counter, Histogram

from fa_search_bot.sites.e621.sendable import E621Post
from fa_search_bot.sites.site_handler import HandlerException, SiteHandler
from fa_search_bot.sites.sent_submission import SentSubmission
from fa_search_bot.sites.site_link import SiteLink
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.utils import gather_ignore_exceptions

if TYPE_CHECKING:
    from typing import Awaitable, List, Optional, Pattern, Union

    from telethon import TelegramClient
    from telethon.tl.custom import InlineBuilder
    from telethon.tl.types import InputBotInlineMessageID, InputBotInlineResultPhoto, TypeInputPeer
    from yippi import AsyncYippiClient, Post

logger = logging.getLogger(__name__)

api_request_times = Histogram(
    "fasearchbot_e6handler_request_time_seconds",
    "Request times of the e621 API, in seconds",
    labelnames=["endpoint"],
)
api_failures = Counter(
    "fasearchbot_e6handler_exceptions_total",
    "Total number of exceptions raised while querying the e621 API",
    labelnames=["endpoint"],
)


class Endpoint(enum.Enum):
    SEARCH = "search"
    SEARCH_MD5 = "search_md5"
    SUBMISSION = "submission"


class E621Handler(SiteHandler):
    POST_LINK = re.compile(r"e(?:621|926)\.net/posts/([0-9]+)", re.I)
    OLD_POST_LINK = re.compile(r"e(?:621|926)\.net/post/show/([0-9]+)", re.I)
    DIRECT_LINK = re.compile(r"e(?:621|926).net/data/(?:sample/)?[0-9a-f]{2}/[0-9a-f]{2}/([0-9a-f]+)")
    E6_LINKS = re.compile(f"({POST_LINK.pattern}|{OLD_POST_LINK.pattern}|{DIRECT_LINK.pattern})")
    POST_HASH = re.compile(r"^[0-9a-f]{32}$", re.I)

    def __init__(self, api: AsyncYippiClient):
        self.api = api
        for endpoint in Endpoint:
            api_request_times.labels(endpoint=endpoint.value)
            api_failures.labels(endpoint=endpoint.value)

    @property
    def site_name(self) -> str:
        return "e621"

    @property
    def site_code(self) -> str:
        return "e6"

    @property
    def link_regex(self) -> Pattern:
        return self.E6_LINKS

    def find_links_in_str(self, haystack: str) -> List[SiteLink]:
        return [SiteLink(self.site_code, match.group(0)) for match in self.E6_LINKS.finditer(haystack)]

    async def get_submission_id_from_link(self, link: SiteLink) -> Optional[SubmissionID]:
        # Handle submission page link matches
        sub_match = self.POST_LINK.match(link.link)
        if sub_match:
            logger.info("e621 link: post link")
            return SubmissionID(self.site_code, sub_match.group(1))
        # Handle thumbnail link matches
        thumb_match = self.OLD_POST_LINK.match(link.link)
        if thumb_match:
            logger.info("e621 link: old post link")
            return SubmissionID(self.site_code, thumb_match.group(1))
        # Handle direct file link matches
        direct_match = self.DIRECT_LINK.match(link.link)
        if not direct_match:
            return None
        md5_hash = direct_match.group(1)
        post = await self._find_post_by_hash(md5_hash)
        if not post:
            raise HandlerException(f"Could not locate the post with hash {md5_hash}.")
        logger.info("e621 link: direct image link")
        return SubmissionID(self.site_code, str(post.id))

    async def _find_post_by_hash(self, md5_hash: str) -> Optional[Post]:
        with api_request_times.labels(endpoint=Endpoint.SEARCH_MD5.value).time():
            with api_failures.labels(endpoint=Endpoint.SEARCH_MD5.value).count_exceptions():
                posts = await self.api.posts(f"md5:{md5_hash}")
        if not posts:
            return None
        return posts[0]

    async def _get_post_by_id(self, sub_id: SubmissionID) -> Optional[Post]:
        with api_request_times.labels(endpoint=Endpoint.SUBMISSION.value).time():
            with api_failures.labels(endpoint=Endpoint.SUBMISSION.value).count_exceptions():
                return await self.api.post(int(sub_id.submission_id))

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
        post = await self._get_post_by_id(SubmissionID(self.site_code, submission_id))
        sendable = E621Post(post)
        return await sendable.send_message(client, chat, reply_to=reply_to, prefix=prefix, edit=edit)

    def link_for_submission(self, submission_id: str) -> str:
        return f"https://e621.net/posts/{submission_id}/"

    def is_valid_submission_id(self, example: str) -> bool:
        try:
            int(example)
            return True
        except ValueError:
            return bool(self.POST_HASH.match(example))

    async def submission_as_answer(
        self, submission_id: SubmissionID, builder: InlineBuilder
    ) -> Awaitable[InputBotInlineResultPhoto]:
        sub_id_str = submission_id.submission_id
        if self.POST_HASH.match(sub_id_str):
            post = await self._find_post_by_hash(sub_id_str)
            if post is None:
                raise HandlerException(f"No e621 submission matches the hash: {sub_id_str}")
        else:
            post = await self._get_post_by_id(submission_id)
        sendable = E621Post(post)
        return sendable.to_inline_query_result(builder)

    async def get_search_results(
        self, builder: InlineBuilder, query: str, page: int
    ) -> List[InputBotInlineResultPhoto]:
        with api_request_times.labels(endpoint=Endpoint.SEARCH.value).time():
            with api_failures.labels(endpoint=Endpoint.SEARCH.value).count_exceptions():
                posts = await self.api.posts(query, page=page)
        return await gather_ignore_exceptions([E621Post(post).to_inline_query_result(builder) for post in posts])
