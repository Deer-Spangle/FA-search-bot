import unittest

from unittest.mock import patch
import telegram

from bot import FASearchBot
from functionalities.welcome import WelcomeFunctionality
from tests.util.mock_telegram_update import MockTelegramUpdate


def test_welcome_message(context):
    update = MockTelegramUpdate.with_command()
    func = WelcomeFunctionality()

    func.call(update, context)

    context.bot.send_message.assert_called()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
    message_text = context.bot.send_message.call_args[1]['text']
    assert "@deerspangle" in message_text
    assert "https://github.com/Deer-Spangle/faexport" in message_text
    assert FASearchBot.VERSION in message_text
