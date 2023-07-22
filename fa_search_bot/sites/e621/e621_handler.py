from __future__ import annotations

import enum
import logging
import re
from typing import TYPE_CHECKING

from prometheus_client.metrics import Counter, Histogram

from fa_search_bot.sites.e621.sendable import E621Post
from fa_search_bot.sites.site_handler import HandlerException, SiteHandler, NotFound
from fa_search_bot.sites.site_link import SiteLink
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.utils import regex_combine

if TYPE_CHECKING:
    from typing import List, Optional, Pattern, Union

    from telethon import TelegramClient
    from telethon.tl.custom import InlineBuilder
    from telethon.tl.types import InputBotInlineMessageID, InputBotInlineResultPhoto, TypeInputPeer
    from yippi import AsyncYippiClient, Post

    from fa_search_bot.sites.sendable import InlineSendable
    from fa_search_bot.sites.sent_submission import SentSubmission

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
    E6_LINKS = regex_combine(POST_LINK, OLD_POST_LINK, DIRECT_LINK)
    E6_FILES = re.compile(r"([0-9a-z]{32})\.(webm|gif|gif\.mp4)")
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

    @property
    def filename_regex(self) -> Pattern:
        return regex_combine(self.E6_FILES, self._fasearchbot_filename_regex)

    def find_links_in_str(self, haystack: str) -> List[SiteLink]:
        return [SiteLink(self.site_code, match.group(0)) for match in self.link_regex.finditer(haystack)]

    def find_filenames_in_str(self, haystack: str) -> List[SiteLink]:
        return [SiteLink(self.site_code, match.group(0)) for match in self.filename_regex.finditer(haystack)]

    async def get_submission_id_from_link(self, link: SiteLink) -> Optional[SubmissionID]:
        # Handle submission page link matches
        sub_match = self.POST_LINK.match(link.link)
        if sub_match:
            sub_id = SubmissionID(self.site_code, sub_match.group(1))
            logger.info("e621 link format: post link: %s", sub_id)
            return sub_id
        # Handle thumbnail link matches
        thumb_match = self.OLD_POST_LINK.match(link.link)
        if thumb_match:
            sub_id = SubmissionID(self.site_code, thumb_match.group(1))
            logger.info("e621 link format: old post link: %s", sub_id)
            return sub_id
        # Handle direct file link matches
        direct_match = self.DIRECT_LINK.match(link.link)
        if not direct_match:
            return None
        md5_hash = direct_match.group(1)
        post = await self._find_post_by_hash(md5_hash)
        if not post:
            raise HandlerException(f"Could not locate the post with hash {md5_hash}.")
        sub_id = SubmissionID(self.site_code, str(post.id))
        logger.info("e621 link format: direct image link: %s", sub_id)
        return sub_id

    async def get_submission_id_from_filename(self, filename: SiteLink) -> Optional[SubmissionID]:
        # Handle FASearchBot filenames
        fas_filename = self._fasearchbot_filename_regex.match(filename.link)
        if fas_filename:
            sub_id = SubmissionID(self.site_code, fas_filename.group(1))
            logger.info("e621 filename format: FASearchBot filename: %s", sub_id)
            return sub_id
        # Handle e621 filenames
        e6_filename = self.E6_FILES.match(filename.link)
        if e6_filename:
            md5_hash = e6_filename.group(1)
            post = await self._find_post_by_hash(md5_hash)
            if post:
                sub_id = SubmissionID(self.site_code, str(post.id))
                logger.info("e621 filename format: e621 filename: %s", sub_id)
                return sub_id
        return None

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
        if post.flags.get("deleted", False):
            raise NotFound("This e621 post has been deleted")
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
    ) -> InputBotInlineResultPhoto:
        sub_id_str = submission_id.submission_id
        if self.POST_HASH.match(sub_id_str):
            post = await self._find_post_by_hash(sub_id_str)
            if post is None:
                raise HandlerException(f"No e621 submission matches the hash: {sub_id_str}")
        else:
            post = await self._get_post_by_id(submission_id)
        sendable = E621Post(post)
        return await sendable.to_inline_query_result(builder)

    async def get_search_results(self, query: str, page: int) -> List[InlineSendable]:
        with api_request_times.labels(endpoint=Endpoint.SEARCH.value).time():
            with api_failures.labels(endpoint=Endpoint.SEARCH.value).count_exceptions():
                posts = await self.api.posts(query, page=page)
        return [E621Post(post) for post in posts]
