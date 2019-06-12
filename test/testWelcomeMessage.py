import unittest

from unittest.mock import patch
import telegram

from bot import FASearchBot
from test.util.testTelegramUpdateObjects import MockTelegramUpdate


class WelcomeTest(unittest.TestCase):

    @patch.object(telegram, "Bot")
    def test_welcome_message(self, bot):
        update = MockTelegramUpdate.with_command()
        searchBot = FASearchBot("config.json")

        searchBot.welcome_message(bot, update)

        bot.send_message.assert_called()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert "@deerspangle" in bot.send_message.call_args[1]['text']
