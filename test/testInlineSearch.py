import unittest

from unittest.mock import patch

import requests_mock
import telegram
from telegram import InlineQueryResultPhoto

from bot import FASearchBot
from test.util.testTelegramUpdateObjects import MockTelegramUpdate

searchBot = FASearchBot("config-test.json")


class NeatenImageTest(unittest.TestCase):

    @patch.object(telegram, "Bot")
    def test_empty_query_no_results(self, bot):
        update = MockTelegramUpdate.with_inline_query(query="")

        searchBot.inline_query(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()
        bot.answer_inline_query.assert_called_with(update.inline_query.id, [])

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_simple_search(self, bot, r):
        post_id = 234563
        update = MockTelegramUpdate.with_inline_query(query="YCH")
        r.get(
            "{}/search.json?full=1&perpage=48&q=ych".format(searchBot.api_url),
            json=[
                {
                    "id": str(post_id),
                    "thumbnail": "thumb-{}.jpg".format(post_id),
                    "link": "link-{}".format(post_id)
                }
            ]
        )

        searchBot.inline_query(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) > 0
        for result in args[1]:
            assert isinstance(result, InlineQueryResultPhoto)
            assert result.id == str(post_id)
            assert result.photo_url == "thumb-{}.jpg".format(post_id)
            assert result.thumb_url == "thumb-{}.jpg".format(post_id)
            assert result.caption == "link-{}".format(post_id)
