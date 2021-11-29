import os

import pytest

from fa_search_bot.sites.fa_export_api import FAExportAPI


@pytest.fixture()
def api() -> FAExportAPI:
    return FAExportAPI(os.getenv('FA_API', 'https://faexport.spangle.org.uk'))
