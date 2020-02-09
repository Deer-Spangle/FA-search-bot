import unittest

from unittest.mock import patch
import telegram

from bot import FASearchBot
from functionalities.welcome import WelcomeFunctionality
from tests.util.mock_telegram_update import MockTelegramUpdate


class WelcomeTest(unittest.TestCase):

    @patch.object(telegram, "Bot")
    def test_welcome_message(self, bot):
        update = MockTelegramUpdate.with_command()
        func = WelcomeFunctionality()

        func.call(bot, update)

        bot.send_message.assert_called()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        message_text = bot.send_message.call_args[1]['text']
        assert "@deerspangle" in message_text
        assert FASearchBot.VERSION in message_text
