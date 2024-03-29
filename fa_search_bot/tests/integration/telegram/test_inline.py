from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from tgintegration import BotController

pytestmark = pytest.mark.asyncio


async def test_inline_query(controller: BotController):
    inline_results = await controller.query_inline("test")
    assert inline_results.results
    assert len(inline_results.results) > 10
    for result in inline_results.results:
        assert result.result.id
        site_code, sub_id = result.result.id.split(":")
        assert site_code == "fa"
        assert result.result.send_message.message
        assert "furaffinity.net/view/" in result.result.send_message.message
        assert sub_id in result.result.send_message.message
        assert result.result.type == "photo"


async def test_inline_gallery_query(controller: BotController):
    inline_results = await controller.query_inline("gallery:dr-spangle")
    assert inline_results.results
    assert len(inline_results.results) > 10
    for result in inline_results.results:
        assert result.result.id
        assert ":" in result.result.id
        sub_id = result.result.id.split(":")[1]
        assert result.result.send_message.message
        assert "furaffinity.net/view/" in result.result.send_message.message
        assert sub_id in result.result.send_message.message
        assert result.result.type == "photo"


async def test_inline_e621_query(controller: BotController):
    inline_results = await controller.query_inline("e621:deer")
    assert inline_results.results
    assert len(inline_results.results) > 10
    for result in inline_results.results:
        assert result.result.id
        site_code, sub_id = result.result.id.split(":")
        assert site_code == "e6"
        assert result.result.send_message.message
        assert "e621.net/posts/" in result.result.send_message.message
        assert sub_id in result.result.send_message.message
        assert result.result.type == "photo"
