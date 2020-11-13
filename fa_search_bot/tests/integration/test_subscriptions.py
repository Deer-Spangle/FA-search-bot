import pytest
from tgintegration import BotController

pytestmark = pytest.mark.asyncio


async def test_subscription_commands(controller: BotController):
    # - create subscription, list subscriptions, remove subscription, list subscriptions

    async with controller.collect(count=1) as response:
        await controller.send_command("add_subscription", ["test"])
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Added subscription: \"test\".")
    lines = response.messages[0].text.html.split("\n")
    assert len(lines) >= 3
    assert "Current subscriptions in this chat:" in lines
    assert "- test" in lines

    async with controller.collect(count=1) as response:
        await controller.send_command("list_subscriptions")
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Current subscriptions in this chat:")
    lines = response.messages[0].text.html.split("\n")
    assert "- test" in lines

    async with controller.collect(count=1) as response:
        await controller.send_command("pause", ["test"])
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Paused subscription: \"test\".")
    lines = response.messages[0].text.html.split("\n")
    assert "- ⏸<s>test</s>" in lines

    async with controller.collect(count=1) as response:
        await controller.send_command("list_subscriptions")
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Current subscriptions in this chat:")
    lines = response.messages[0].text.html.split("\n")
    assert "- ⏸<s>test</s>" in lines

    async with controller.collect(count=1) as response:
        await controller.send_command("resume", ["test"])
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Resumed subscription: \"test\".")
    lines = response.messages[0].text.html.split("\n")
    assert "- test" in lines

    async with controller.collect(count=1) as response:
        await controller.send_command("list_subscriptions")
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Current subscriptions in this chat:")
    lines = response.messages[0].text.html.split("\n")
    assert "- test" in lines

    async with controller.collect(count=1) as response:
        await controller.send_command("remove_subscription", ["test"])
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Removed subscription: \"test\".")
    lines = response.messages[0].text.html.split("\n")
    assert "- test" not in lines

    async with controller.collect(count=1) as response:
        await controller.send_command("list_subscriptions")
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Current subscriptions in this chat:")
    lines = response.messages[0].text.html.split("\n")
    assert "- test" not in lines


async def test_block_commands(controller: BotController):
    # - create block, list blocks, remove block, list blocks
    async with controller.collect(count=1) as response:
        await controller.send_command("add_blocklisted_tag", ["test"])
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Added tag to blocklist: \"test\".")
    lines = response.messages[0].text.html.split("\n")
    assert "Current blocklist for this chat:" in lines
    assert "- test" in lines

    async with controller.collect(count=1) as response:
        await controller.send_command("list_blocklisted_tags")
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Current blocklist for this chat:")
    lines = response.messages[0].text.html.split("\n")
    assert "- test" in lines

    async with controller.collect(count=1) as response:
        await controller.send_command("remove_blocklisted_tag", ["test"])
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Removed tag from blocklist: \"test\".")
    lines = response.messages[0].text.html.split("\n")
    assert "Current blocklist for this chat:" in lines
    assert "- test" not in lines

    async with controller.collect(count=1) as response:
        await controller.send_command("list_blocklisted_tags")
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Current blocklist for this chat:")
    lines = response.messages[0].text.html.split("\n")
    assert "- test" not in lines
