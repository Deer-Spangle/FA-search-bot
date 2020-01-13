import unittest

from unittest.mock import patch
import telegram
from telegram import Chat

from bot import ImageHashRecommendFunctionality
from tests.util.mock_telegram_update import MockTelegramUpdate


class WelcomeTest(unittest.TestCase):

    @patch.object(telegram, "Bot")
    def test_sends_recommendation(self, bot):
        update = MockTelegramUpdate.with_message(text=None).with_photo()
        func = ImageHashRecommendFunctionality()

        func.call(bot, update)

        bot.send_message.assert_called()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        message_text = bot.send_message.call_args[1]['text']
        assert "@FindFurryPicBot" in message_text

    @patch.object(telegram, "Bot")
    def test_no_reply_in_group(self, bot):
        update = MockTelegramUpdate.with_message(
            text=None,
            chat_type=Chat.GROUP
        ).with_photo()
        func = ImageHashRecommendFunctionality()

        func.call(bot, update)

        bot.send_message.assert_not_called()
