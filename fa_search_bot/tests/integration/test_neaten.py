import pytest


async def test_start(controller):
    # - Get start message
    async with controller.collect(count=1) as response:
        await controller.send_command("/start")

    assert response.num_messages == 1
    assert "@deerspangle" in response.messages[0].text


async def test_neaten_link(controller):
    # - send link, get neatened pic
    async with controller.collect(count=2) as response:
        # TODO: swap if send_message() gets added to BotController
        await controller.client.send_message(controller.peer_id, "https://www.furaffinity.net/view/19925704/")

    assert response.num_messages == 2
    assert response.messages[0].text.startswith("⏳")
    assert "19925704" in response.messages[-1].caption
    assert response.messages[-1].photo


@pytest.mark.skip("Not sure how to test in group yet.")
def test_neaten_link_in_group():
    # TODO
    # - neaten link in group
    assert False
    pass


@pytest.mark.skip("Not sure how to test in group yet.")
def test_no_neaten_caption_in_group():
    # TODO
    # - in group neaten doesn't reply to image with caption link
    assert False
    pass
