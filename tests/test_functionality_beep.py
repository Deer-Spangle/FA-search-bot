import unittest

from unittest.mock import patch, MagicMock

import pytest
import telegram

from functionalities.beep import BeepFunctionality
from tests.util.mock_telegram_update import MockTelegramUpdate


@pytest.fixture
def context():
    context = MagicMock()
    context.bot = MagicMock()
    return context


def test_beep(context):
    update = MockTelegramUpdate.with_command()
    beep = BeepFunctionality()

    beep.call(update, context)

    context.bot.send_message.assert_called()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_message.call_args[1]['text'] == "boop"
