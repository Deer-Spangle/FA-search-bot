import pytest
from pyrogram.raw.functions.messages import MigrateChat
from pyrogram.types import Chat
from tgintegration import BotController

pytestmark = pytest.mark.asyncio


async def test_subscription_commands(controller: BotController):
    # - create subscription, list subscriptions, remove subscription, list subscriptions

    async with controller.collect(count=1) as response:
        await controller.send_command("add_subscription", ["test"])
    assert response.num_messages == 1
    assert response.messages[0].text.startswith('Added subscription: "test".')
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
    assert response.messages[0].text.startswith('Paused subscription: "test".')
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
    assert response.messages[0].text.startswith('Resumed subscription: "test".')
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
    assert response.messages[0].text.startswith('Removed subscription: "test".')
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
    assert response.messages[0].text.startswith('Added tag to blocklist: "test".')
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
    assert response.messages[0].text.startswith('Removed tag from blocklist: "test".')
    lines = response.messages[0].text.html.split("\n")
    assert "Current blocklist for this chat:" in lines
    assert "- test" not in lines

    async with controller.collect(count=1) as response:
        await controller.send_command("list_blocklisted_tags")
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Current blocklist for this chat:")
    lines = response.messages[0].text.html.split("\n")
    assert "- test" not in lines


async def test_group_migration(controller: BotController, group_chat: Chat):
    # Create subscription
    async with controller.collect(count=1, peer=group_chat.id) as response:
        await controller.send_command("add_subscription", ["test"], peer=group_chat.id)
    assert response.num_messages == 1
    assert response.messages[0].text.startswith('Added subscription: "test".')
    lines = response.messages[0].text.html.split("\n")
    assert len(lines) >= 3
    assert "Current subscriptions in this chat:" in lines
    assert "- test" in lines

    # List subscriptions
    async with controller.collect(count=1, peer=group_chat.id) as response:
        await controller.send_command("list_subscriptions", peer=group_chat.id)
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Current subscriptions in this chat:")
    lines = response.messages[0].text.html.split("\n")
    assert "- test" in lines

    # Migrate chat to supergroup
    updates = await controller.client.send(MigrateChat(chat_id=abs(group_chat.id)))
    new_chat_id = int(f"-100{[chat.id for chat in updates.chats if chat.id != abs(group_chat.id)][0]}")
    group_chat.id = new_chat_id

    # List subscriptions
    async with controller.collect(count=1, peer=new_chat_id) as response:
        await controller.send_command("list_subscriptions", peer=new_chat_id)
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Current subscriptions in this chat:")
    lines = response.messages[0].text.html.split("\n")
    assert "- test" in lines

    # Delete subscription
    async with controller.collect(count=1, peer=new_chat_id) as response:
        await controller.send_command("remove_subscription", ["test"], peer=new_chat_id)
    assert response.num_messages == 1
    assert response.messages[0].text.startswith('Removed subscription: "test".')
    lines = response.messages[0].text.html.split("\n")
    assert "- test" not in lines

    # List subscriptions
    async with controller.collect(count=1, peer=new_chat_id) as response:
        await controller.send_command("list_subscriptions", peer=new_chat_id)
    assert response.num_messages == 1
    assert response.messages[0].text.startswith("Current subscriptions in this chat:")
    lines = response.messages[0].text.html.split("\n")
    assert "- test" not in lines
