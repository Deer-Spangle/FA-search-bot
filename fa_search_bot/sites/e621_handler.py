import enum
import logging
import re
from typing import Coroutine, List, Optional, Pattern, Union

from prometheus_client.metrics import Counter, Histogram
from telethon import TelegramClient
from telethon.tl.custom import InlineBuilder
from telethon.tl.types import InputBotInlineMessageID, InputBotInlineResultPhoto, TypeInputPeer
from yippi import AsyncYippiClient, Post

from fa_search_bot.sites.sendable import CaptionSettings, Sendable
from fa_search_bot.sites.site_handler import HandlerException, SiteHandler

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

    def find_links_in_str(self, haystack: str) -> List[str]:
        return [match.group(0) for match in self.E6_LINKS.finditer(haystack)]

    async def get_submission_id_from_link(self, link: str) -> Optional[int]:
        # Handle submission page link matches
        sub_match = self.POST_LINK.match(link)
        if sub_match:
            logger.info("e621 link: post link")
            return int(sub_match.group(1))
        # Handle thumbnail link matches
        thumb_match = self.OLD_POST_LINK.match(link)
        if thumb_match:
            logger.info("e621 link: old post link")
            return int(thumb_match.group(1))
        # Handle direct file link matches
        direct_match = self.DIRECT_LINK.match(link)
        if not direct_match:
            return None
        md5_hash = direct_match.group(1)
        post = await self._find_post_by_hash(md5_hash)
        if not post:
            raise HandlerException(f"Could not locate the post with hash {md5_hash}.")
        logger.info("e621 link: direct image link")
        return post.id

    async def _find_post_by_hash(self, md5_hash: str) -> Optional[Post]:
        with api_request_times.labels(endpoint=Endpoint.SEARCH_MD5.value).time():
            with api_failures.labels(endpoint=Endpoint.SEARCH_MD5.value).count_exceptions():
                posts = await self.api.posts(f"md5:{md5_hash}")
        if not posts:
            return None
        return posts[0]

    async def _get_post_by_id(self, post_id: Union[int, str]) -> Optional[Post]:
        with api_request_times.labels(endpoint=Endpoint.SUBMISSION.value).time():
            with api_failures.labels(endpoint=Endpoint.SUBMISSION.value).count_exceptions():
                return await self.api.post(post_id)

    async def send_submission(
            self,
            submission_id: int,
            client: TelegramClient,
            chat: Union[TypeInputPeer, InputBotInlineMessageID],
            *,
            reply_to: Optional[int] = None,
            prefix: str = None,
            edit: bool = False,
    ) -> None:
        post = await self._get_post_by_id(submission_id)
        sendable = E621Post(post)
        await sendable.send_message(client, chat, reply_to=reply_to, prefix=prefix, edit=edit)

    def link_for_submission(self, submission_id: int) -> str:
        return f"https://e621.net/posts/{submission_id}/"

    def is_valid_submission_id(self, example: str) -> bool:
        try:
            int(example)
            return True
        except ValueError:
            return bool(self.POST_HASH.match(example))

    async def submission_as_answer(
            self, submission_id: Union[int, str], builder: InlineBuilder
    ) -> Coroutine[None, None, InputBotInlineResultPhoto]:
        sub_id_str = str(submission_id)
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
    ) -> List[Coroutine[None, None, InputBotInlineResultPhoto]]:
        with api_request_times.labels(endpoint=Endpoint.SEARCH.value).time():
            with api_failures.labels(endpoint=Endpoint.SEARCH.value).count_exceptions():
                posts = await self.api.posts(query, page=page)
        return [E621Post(post).to_inline_query_result(builder) for post in posts]


class E621Post(Sendable):
    def __init__(self, post: Post):
        self.post = post

    @property
    def site_id(self) -> str:
        return "e6"

    @property
    def id(self) -> str:
        return str(self.post.id)

    @property
    def download_url(self) -> str:
        return self.post.file["url"]

    @property
    def download_file_ext(self) -> str:
        return self.post.file["ext"].lower()

    @property
    def download_file_size(self) -> int:
        return self.post.file["size"]

    @property
    def preview_image_url(self) -> str:
        if self.download_file_ext == "swf":
            return self.post.preview["url"]
        if self.download_file_ext == "webm":
            return self.post.sample["url"]
        return self.download_url

    @property
    def thumbnail_url(self) -> str:
        if self.download_file_ext == "swf":
            return self.post.preview["url"]
        return self.post.sample["url"]

    @property
    def link(self) -> str:
        return f"https://e621.net/posts/{self.id}"

    def caption(self, settings: CaptionSettings, prefix: Optional[str] = None) -> str:
        lines = []
        if prefix:
            lines.append(prefix)
        lines.append(self.link)
        if settings.direct_link:
            lines.append(f"<a href=\"{self.post.file['url']}\">Direct download</a>")
        return "\n".join(lines)
