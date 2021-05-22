from asyncio import Future
from unittest.mock import Mock

import pytest
from telegram import Message
from telegram.ext import CallbackContext
from telegram.utils.promise import Promise
from telethon import TelegramClient

from fa_search_bot.mqbot import MQBot


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


@pytest.fixture
def context():
    sent_message_ids = range(34243234, 34244234, 27)
    context = Mock(CallbackContext)
    context._sent_message_ids = sent_message_ids
    context.attach_mock(Mock(MQBot), "bot")
    context.bot = Mock(MQBot)
    context.bot.send_message.side_effect = [mock_message_promise(m) for m in sent_message_ids]
    return context
