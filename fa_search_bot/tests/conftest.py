from asyncio import Future
from unittest.mock import Mock

import pytest
from telegram import Message
from telegram.utils.promise import Promise
from telethon import TelegramClient


class MockChat:
    def __init__(self, chat_id: int):
        self.chat_id = chat_id


def mock_message_promise(message_id):
    promise = Mock(Promise)
    message = Mock(Message)
    promise.result.return_value = message
    message.message_id = message_id
    return promise


@pytest.fixture
def mock_client():
    client = Mock(TelegramClient, return_value=Future())
    return client
