from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

from fa_search_bot.sites.furaffinity.fa_handler import FAHandler

if TYPE_CHECKING:
    from fa_search_bot.sites.furaffinity.fa_export_api import FAExportAPI


class MockSiteHandler(FAHandler):
    def __init__(
        self,
        api: FAExportAPI,
        *,
        site_name: str = None,
        site_code: str = None,
    ):
        super().__init__(api)
        self._site_name = site_name or "MockSite"
        self._site_code = site_code or "mk"
        self._send_submission = AsyncMock()

    @property
    def site_name(self) -> str:
        return self._site_name

    @property
    def site_code(self) -> str:
        return self._site_code

    async def send_submission(self, *args, **kwargs) -> None:
        await self._send_submission(*args, **kwargs)
