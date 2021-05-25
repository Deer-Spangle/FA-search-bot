import asyncio
import os
import sys
import time
from threading import Thread

import pytest
from pyrogram import Client
from pyrogram.types import Chat
from tgintegration import BotController

from fa_search_bot.bot import FASearchBot


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
        os.getenv("CLIENT_SESSION_STRING"),
        api_id=os.getenv("CLIENT_API_ID"),
        api_hash=os.getenv("CLIENT_API_HASH")
    )
    await client.start()
    yield client
    await client.stop()


@pytest.fixture(scope="session")
def bot() -> FASearchBot:
    bot = FASearchBot(os.getenv('CONFIG_FILE', 'config.json'))
    if os.getenv("BOT_KEY"):
        bot.config.telegram.bot_key = os.getenv("BOT_KEY")
    if os.getenv("CLIENT_API_ID"):
        bot.config.telegram.api_id = os.getenv("CLIENT_API_ID")
    if os.getenv("CLIENT_API_HASH"):
        bot.config.telegram.api_hash = os.getenv("CLIENT_API_HASH")
    bot_thread = Thread(target=bot.start)
    bot_thread.start()
    while not bot.alive:
        asyncio.sleep(0.1)
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
    return controller


@pytest.fixture(scope="session")
async def group_chat(client, bot) -> Chat:
    group = await client.create_group("Automated test group", [bot.bot.username])
    yield group
    await client.leave_chat(group.id, delete=True)
