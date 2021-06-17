import logging
import re
from typing import Union, Optional, List, Pattern, Coroutine

from telethon import TelegramClient
from telethon.tl.custom import InlineBuilder
from telethon.tl.types import TypeInputPeer, InputBotInlineMessageID, InputBotInlineResultPhoto
from yippi import AsyncYippiClient, Post

from fa_search_bot.sites.fa_submission import CaptionSettings
from fa_search_bot.sites.sendable import Sendable
from fa_search_bot.sites.site_handler import SiteHandler, HandlerException

logger = logging.getLogger(__name__)


class E621Handler(SiteHandler):
    POST_LINK = re.compile(r"e621\.net/posts/([0-9]+)", re.I)
    OLD_POST_LINK = re.compile(r"e621\.net/post/show/([0-9]+)", re.I)
    DIRECT_LINK = re.compile(r"e621.net/data/[0-9a-f]{2}/[0-9a-f]{2}/([0-9a-f]+)")
    E6_LINKS = re.compile(f"({POST_LINK.pattern}|{OLD_POST_LINK.pattern}|{DIRECT_LINK.pattern})")

    def __init__(self, api: AsyncYippiClient):
        self.api = api

    @property
    def link_regex(self) -> Pattern:
        return self.E6_LINKS

    def find_links_in_str(self, haystack: str) -> List[str]:
        return [match[0] for match in self.E6_LINKS.findall(haystack)]

    async def get_submission_id_from_link(self, link: str) -> int:
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
        md5_hash = direct_match.group(1)
        post_id = await self._find_post_by_hash(md5_hash)
        if not post_id:
            raise HandlerException(
                f"Could not locate the post with hash {md5_hash}."
            )
        logger.info("e621 link: direct image link")
        return post_id

    async def _find_post_by_hash(self, md5_hash: str) -> Optional[int]:
        posts = await self.api.posts(f"md5:{md5_hash}")
        if not posts:
            return None
        return posts[0].id

    async def send_submission(
            self,
            submission_id: int,
            client: TelegramClient,
            chat: Union[TypeInputPeer, InputBotInlineMessageID],
            *,
            reply_to: Optional[int] = None,
            prefix: str = None,
            edit: bool = False
    ) -> None:
        post = await self.api.post(submission_id)
        sendable = E621Post(post)
        await sendable.send_message(client, chat, reply_to=reply_to, prefix=prefix, edit=edit)

    def is_valid_submission_id(self, example: str) -> bool:
        try:
            int(example)
            return True
        except ValueError:
            return False

    async def submission_as_answer(
            self,
            submission_id: Union[int, str],
            builder: InlineBuilder
    ) -> Coroutine[None, None, InputBotInlineResultPhoto]:
        post = await self.api.post(submission_id)
        sendable = E621Post(post)
        return sendable.to_inline_query_result(builder)


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
        return self.post.file["ext"]

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
        lines.append(f"https://e621.net/posts/{self.post.id}/")
        if settings.direct_link:
            lines.append(f"<a href=\"{self.post.file['url']}\">Direct download</a>")
        return "\n".join(lines)
