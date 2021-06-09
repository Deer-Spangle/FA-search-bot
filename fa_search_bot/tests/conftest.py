import random
from asyncio import Future
from unittest.mock import Mock

import pytest
from telethon import TelegramClient


class MockChat:
    def __init__(self, chat_id: int):
        self.chat_id = chat_id


@pytest.fixture
def mock_client():
    client = Mock(TelegramClient, return_value=Future())
    return client
