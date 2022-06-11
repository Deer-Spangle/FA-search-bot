import asyncio
import os
import sys
import time
from typing import TYPE_CHECKING

import pytest
from pyrogram import Client
from tgintegration import BotController

from fa_search_bot.bot import Config, FASearchBot

if TYPE_CHECKING:
    from pyrogram.types import Chat


@pytest.fixture(scope="session", autouse=True)
def event_loop(request):
    """Create an instance of the default event loop for the session."""
    if sys.platform == "win32":
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
        api_hash=os.getenv("CLIENT_API_HASH"),
    )
    await client.start()
    yield client
    await client.stop()


@pytest.fixture(scope="session")
def bot() -> FASearchBot:
    config = Config.load_from_file(os.getenv("CONFIG_FILE", "config.json"))
    if os.getenv("BOT_KEY"):
        config.telegram.bot_token = os.getenv("BOT_KEY")
    if os.getenv("CLIENT_API_ID"):
        config.telegram.api_id = os.getenv("CLIENT_API_ID")
    if os.getenv("CLIENT_API_HASH"):
        config.telegram.api_hash = os.getenv("CLIENT_API_HASH")
    if os.getenv("E621_USERNAME"):
        config.e621.username = os.getenv("E621_USERNAME")
    if os.getenv("E621_API_KEY"):
        config.e621.api_key = os.getenv("E621_API_KEY")
    bot = FASearchBot(config)
    bot.api.MAX_RETRIES = 3
    bot.start()
    while not bot.alive:
        time.sleep(0.1)
    yield bot
    bot.alive = False
    bot.close()


@pytest.fixture
async def controller(client, bot) -> BotController:
    bot_user = await bot.client.get_me()
    controller = BotController(peer=bot_user.username, client=client)
    await controller.initialize(start_client=False)
    return controller


@pytest.fixture(scope="session")
async def group_chat(client, bot) -> Chat:
    bot_user = await bot.client.get_me()
    group = await client.create_group("Automated test group", [bot_user.username])
    yield group
    await client.leave_chat(group.id, delete=True)
