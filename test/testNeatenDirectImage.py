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
    def test_ignore_message(self, bot):
        update = MockTelegramUpdate.with_message(text="hello world")

        searchBot.neaten_direct_image(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_ignore_link(self, bot):
        update = MockTelegramUpdate.with_message(text="http://example.com")

        searchBot.neaten_direct_image(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_ignore_profile_link(self, bot):
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/user/fender/")

        searchBot.neaten_direct_image(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_ignore_journal_link(self, bot):
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/journal/9150534/")

        searchBot.neaten_direct_image(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_ignore_submission_link(self, bot):
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/23636984/")

        searchBot.neaten_direct_image(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_direct_link(self, bot, r):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        r.get(
            "{}/user/{}/gallery.json?page=1&full=1".format(searchBot.api_url, username),
            json=[
                {
                    "id": post_id,
                    "thumbnail": "http://url.com/thumb@400-{}.jpg".format(image_id)
                },
                {
                    "id": post_id-1,
                    "thumbnail": "http://url.com/thumb@300-{}.jpg".format(image_id-15)
                }
            ]
        )
        r.get(
            "{}/submission/{}.json".format(searchBot.api_url, sub_id),
            json={
                "download": "dl-{}.jpg".format(post_id),
                "link": "link-{}".format(post_id)
            }
        )

        searchBot.neaten_direct_image(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == "dl-{}.jpg".format(post_id)
        assert bot.send_photo.call_args[1]['caption'] == "link-{}".format(post_id)
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id
