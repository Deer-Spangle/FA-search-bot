from typing import Dict, Optional

import requests

from fa_search_bot.sites.sendable import Sendable, CaptionSettings
from fa_search_bot.sites.submission_id import SubmissionID


class WeasylPost(Sendable):

    def __init__(self, post_data: Dict) -> None:
        self.post_data = post_data
        self._download_file_size: Optional[int] = None

    @property
    def submission_id(self) -> SubmissionID:
        return SubmissionID("wzl", str(self.post_data["submitid"]))

    @property
    def download_url(self) -> str:
        return self.post_data["media"]["submission"][0]["url"]

    @property
    def download_file_ext(self) -> str:
        return self.download_url.split(".")[-1].lower()

    @property
    def download_file_size(self) -> int:
        if self._download_file_size is None:
            resp = requests.head(self.download_url)
            self._download_file_size = int(resp.headers.get("content-length", 0))
        return self._download_file_size

    @property
    def preview_image_url(self) -> str:
        return self.post_data["media"]["cover"][0]["url"]

    @property
    def title(self) -> Optional[str]:
        return self.post_data["title"]

    @property
    def author(self) -> Optional[str]:
        return self.post_data["owner"]

    def caption(self, settings: CaptionSettings, prefix: Optional[str] = None) -> str:
        lines = []
        if prefix:
            lines.append(prefix)
        if settings.title:
            lines.append(f'"{self.title}"')
        if settings.author:
            author_link = f"https://www.weasyl.com/~{self.post_data['owner_login']}]"
            lines.append(f'By: <a href="{author_link}">{self.author}</a>')
        lines.append(self.link)
        if settings.direct_link:
            lines.append(f'<a href="{self.download_url}">Direct download</a>')
        return "\n".join(lines)

    @property
    def thumbnail_url(self) -> str:
        return self.post_data["media"]["thumbnail"][0]["url"]

    @property
    def link(self) -> str:
        return f"https://www.weasyl.com/submission/{self.submission_id.submission_id}/"
