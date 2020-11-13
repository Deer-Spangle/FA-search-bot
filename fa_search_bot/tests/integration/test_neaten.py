import pytest
from tgintegration import BotController

pytestmark = pytest.mark.asyncio


async def test_neaten_link(controller: BotController):
    # - send link, get neatened pic
    async with controller.collect(count=2) as response:
        # TODO: swap if send_message() gets added to BotController
        await controller.client.send_message(controller.peer_id, "https://www.furaffinity.net/view/19925704/")

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert "19925704" in response.messages[-1].caption
    assert response.messages[-1].photo


async def test_neaten_link_in_group(controller: BotController):
    # - neaten link in group
    # Todo: create group if not exists?
    group_id = -1001295266389
    # - send link, get neatened pic
    async with controller.collect(count=2, peer=group_id) as response:
        await controller.client.send_message(group_id, "https://www.furaffinity.net/view/19925704/")

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert "19925704" in response.messages[-1].caption
    assert response.messages[-1].photo


async def test_no_neaten_caption_in_group(controller: BotController):
    # - in group neaten doesn't reply to image with caption link
    # Todo: create group if not exists?
    group_id = -1001295266389
    thumb_link = "https://t.facdn.net/19925704@400-1462827244.jpg"
    async with controller.collect(peer=group_id, raise_=False) as response:
        await controller.client.send_photo(group_id, thumb_link, caption="https://www.furaffinity.net/view/19925704/")

    assert response.num_messages == 0
