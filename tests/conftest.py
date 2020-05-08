from unittest.mock import Mock

import pytest
from telegram import Bot, Message
from telegram.ext import CallbackContext


def mock_message(message_id):
    mock = Mock(Message)
    mock.message_id = message_id
    return mock


@pytest.fixture
def context():
    sent_message_ids = range(34243234, 34244234, 27)
    context = Mock(CallbackContext)
    context._sent_message_ids = sent_message_ids
    context.attach_mock(Mock(Bot), "bot")
    context.bot = Mock(Bot)
    context.bot.send_message.side_effect = [mock_message(m) for m in sent_message_ids]
    return context
