from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from fa_search_bot.sites.sendable import Sendable, CaptionSettings, InlineSendable
from fa_search_bot.sites.submission_id import SubmissionID

if TYPE_CHECKING:
    from fa_search_bot.sites.furaffinity.fa_submission import FASubmissionFull, FASubmissionShort


class InlineSendableFASubmission(InlineSendable):
    def __init__(self, submission: FASubmissionShort) -> None:
        self.submission = submission

    @property
    def submission_id(self) -> SubmissionID:
        return SubmissionID("fa", self.submission.submission_id)

    @property
    def thumbnail_url(self) -> str:
        return self.submission.thumbnail_url

    @property
    def link(self) -> str:
        return self.submission.link


class SendableFASubmission(Sendable):
    def __init__(self, submission: FASubmissionFull):
        super().__init__()
        self.submission = submission

    @property
    def submission_id(self) -> SubmissionID:
        return SubmissionID("fa", self.submission.submission_id)

    @property
    def download_url(self) -> str:
        return self.submission.download_url

    @property
    def download_file_ext(self) -> str:
        return self.submission.download_file_ext

    async def download_file_size(self) -> int:
        return await self.submission.download_file_size()

    @property
    def preview_image_url(self) -> str:
        return self.submission.full_image_url

    @property
    def author(self) -> Optional[str]:
        return self.submission.author.name

    @property
    def title(self) -> Optional[str]:
        return self.submission.title

    @property
    def thumbnail_url(self) -> str:
        return self.submission.thumbnail_url

    @property
    def link(self) -> str:
        return self.submission.link

    def caption(self, settings: CaptionSettings, prefix: Optional[str] = None) -> str:
        lines = []
        if prefix:
            lines.append(prefix)
        if settings.title:
            lines.append(f'"{self.submission.title}"')
        if settings.author:
            lines.append(f'By: <a href="{self.submission.author.link}">{self.submission.author.name}</a>')
        lines.append(self.submission.link)
        if settings.direct_link:
            lines.append(f'<a href="{self.download_url}">Direct download</a>')
        return "\n".join(lines)
