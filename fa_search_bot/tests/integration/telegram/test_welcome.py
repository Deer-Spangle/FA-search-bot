from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from tgintegration import BotController

pytestmark = pytest.mark.asyncio


async def test_start(controller: BotController):
    # - Get start message
    async with controller.collect(count=1) as response:
        await controller.send_command("/start")

    assert response.num_messages == 1
    assert "@deerspangle" in response.messages[0].text
