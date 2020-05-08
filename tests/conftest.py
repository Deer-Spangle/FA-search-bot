from unittest.mock import Mock

import pytest
from telegram import Bot, Message
from telegram.ext import CallbackContext
from telegram.utils.promise import Promise


def mock_message_promise(message_id):
    promise = Mock(Promise)
    message = Mock(Message)
    promise.result.return_value = message
    message.message_id = message_id
    return promise


@pytest.fixture
def context():
    sent_message_ids = range(34243234, 34244234, 27)
    context = Mock(CallbackContext)
    context._sent_message_ids = sent_message_ids
    context.attach_mock(Mock(Bot), "bot")
    context.bot = Mock(Bot)
    context.bot.send_message.side_effect = [mock_message_promise(m) for m in sent_message_ids]
    return context
