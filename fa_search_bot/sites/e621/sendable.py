from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from fa_search_bot.sites.sendable import Sendable, CaptionSettings
from fa_search_bot.sites.submission_id import SubmissionID

if TYPE_CHECKING:
    from yippi import Post


class E621Post(Sendable):
    def __init__(self, post: Post):
        super().__init__()
        self.post = post

    @property
    def submission_id(self) -> SubmissionID:
        return SubmissionID("e6", str(self.post.id))

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
