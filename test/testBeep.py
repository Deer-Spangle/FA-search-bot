import unittest

from unittest.mock import patch
import telegram

from bot import FASearchBot
from test.util.testTelegramUpdateObjects import MockTelegramUpdate


class MockObjectsTest(unittest.TestCase):

    @patch.object(telegram, "Bot")
    def test_beep(self, bot):
        update = MockTelegramUpdate.with_command()
        searchBot = FASearchBot("config.json")

        searchBot.beep(bot, update)

        bot.send_message.assert_called()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == "boop"
