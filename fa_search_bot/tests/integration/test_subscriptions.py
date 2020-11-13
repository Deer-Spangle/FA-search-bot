import pytest
from tgintegration import BotController

from fa_search_bot.bot import FASearchBot

pytestmark = pytest.mark.asyncio


async def test_subscription_commands(controller: BotController, bot: FASearchBot):
    # - create subscription, list subscriptions, remove subscription, list subscriptions

    async with controller.collect(count=1) as response:
        await controller.send_command("add_subscription", ["test"])

    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Added subscription: \"test\".")
    lines = response.messages[0].text.split("\n")
    assert len(lines) >= 3
    assert "Current subscriptions in this chat:" in lines
    assert "- test" in lines

    async with controller.collect(count=1) as response:
        await controller.send_command("list_subscriptions")

    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Current subscriptions in this chat:")
    lines = response.messages[0].text.split("\n")
    assert "- test" in lines

    async with controller.collect(count=1) as response:
        await controller.send_command("remove_subscription", ["test"])

    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Removed subscription: \"test\".")
    lines = response.messages[0].text.split("\n")
    assert "- test" not in lines

    async with controller.collect(count=1) as response:
        await controller.send_command("list_subscriptions")

    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Current subscriptions in this chat:")
    lines = response.messages[0].text.split("\n")
    assert "- test" not in lines

# - create block, list blocks, remove block, list blocks
