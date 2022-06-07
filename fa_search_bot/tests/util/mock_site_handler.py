from unittest.mock import AsyncMock

from fa_search_bot.sites.fa_export_api import FAExportAPI
from fa_search_bot.sites.fa_handler import FAHandler


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
