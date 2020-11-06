import asyncio
import sys
import time
from threading import Thread

import pytest
from pyrogram import Client
from tgintegration import BotController

from fa_search_bot.bot import FASearchBot

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="session", autouse=True)
def event_loop(request):
    """ Create an instance of the default event loop for the session. """
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def client() -> Client:
    client = Client(
        "test_client",
        api_id=877887,
        api_hash="7ed46f591fd8cd642e7b749a796753fc"
    )
    await client.start()
    yield client
    await client.stop()


@pytest.fixture(scope="session")
async def bot() -> FASearchBot:
    bot = FASearchBot("config.json")
    bot_thread = Thread(target=bot.start)
    bot_thread.start()
    while not bot.alive:
        time.sleep(0.1)
    yield bot
    bot.alive = False
    bot_thread.join()


@pytest.fixture
async def controller(client, bot) -> BotController:
    controller = BotController(
        peer=bot.bot.username,
        client=client
    )
    await controller.initialize(start_client=False)
    yield controller


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
