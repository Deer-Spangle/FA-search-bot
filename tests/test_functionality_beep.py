import unittest

from unittest.mock import patch
import telegram

from functionalities.beep import BeepFunctionality
from tests.util.mock_telegram_update import MockTelegramUpdate


class BeepTest(unittest.TestCase):

    @patch.object(telegram, "Bot")
    def test_beep(self, bot):
        update = MockTelegramUpdate.with_command()
        beep = BeepFunctionality()

        beep.call(bot, update)

        bot.send_message.assert_called()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == "boop"
