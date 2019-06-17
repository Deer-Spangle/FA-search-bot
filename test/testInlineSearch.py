import unittest

from unittest.mock import patch, call

import requests_mock
import telegram
from telegram import Chat

from bot import FASearchBot
from test.util.testTelegramUpdateObjects import MockTelegramUpdate

searchBot = FASearchBot("config-test.json")


class NeatenImageTest(unittest.TestCase):

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_empty_query_lists_home(self, bot, r):
        update = MockTelegramUpdate.with_inline_query(query="")

        searchBot.inline_query(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()
        bot.answer_inline_query.assert_not_called()
