import pytest
from tgintegration import BotController

pytestmark = pytest.mark.asyncio


async def test_inline_id_query(controller: BotController):
    inline_results = await controller.query_inline("19925704")
    assert inline_results.results
    assert len(inline_results.results) == 1
    result = inline_results.results[0]
    assert result.id == "19925704"
    assert result.result.type == "photo"
    assert result.result.photo


async def test_inline_link_query(controller: BotController):
    inline_results = await controller.query_inline("https://www.furaffinity.net/view/19925704/")
    assert inline_results.results
    assert len(inline_results.results) == 1
    result = inline_results.results[0]
    assert result.id == "19925704"
    assert result.result.type == "photo"
    assert result.result.photo