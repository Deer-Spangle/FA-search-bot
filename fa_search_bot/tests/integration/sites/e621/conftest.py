import pytest
from yippi import AsyncYippiClient

from fa_search_bot._version import __VERSION__


@pytest.fixture  # (scope="session")
def yippi_client():
    client = AsyncYippiClient("FASearchBot integration test", __VERSION__, "dr-spangle")
    yield client
    client.close()
