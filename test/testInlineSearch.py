import unittest

from unittest.mock import patch

import requests_mock
import telegram
from telegram import InlineQueryResultPhoto, InlineQueryResultArticle, InputMessageContent

from bot import FASearchBot
from test.util.mock_export_api import MockSubmission, MockExportAPI
from test.util.testTelegramUpdateObjects import MockTelegramUpdate

searchBot = FASearchBot("config-test.json")


class NeatenImageTest(unittest.TestCase):

    def setUp(self) -> None:
        searchBot.api = MockExportAPI()

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
        search_term = "YCH"
        update = MockTelegramUpdate.with_inline_query(query=search_term)
        submission = MockSubmission(post_id)
        searchBot.api.with_search_results(search_term, [submission])

        searchBot.inline_query(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == 2
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) > 0
        for result in args[1]:
            assert isinstance(result, InlineQueryResultPhoto)
            assert result.id == str(post_id)
            assert result.photo_url == submission.thumbnail_url
            assert result.thumb_url == submission.thumbnail_url
            assert result.caption == submission.link

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_no_search_results(self, bot, r):
        search_term = "RareKeyword"
        update = MockTelegramUpdate.with_inline_query(query=search_term)
        searchBot.api.with_search_results(search_term, [])

        searchBot.inline_query(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == ""
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultArticle)
        assert args[1][0].title == "No results found."
        assert isinstance(args[1][0].input_message_content, InputMessageContent)
        assert args[1][0].input_message_content.message_text == "No results for search \"{}\".".format(search_term)

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_search_with_offset(self, bot, r):
        post_id = 234563
        search_term = "YCH"
        offset = 2
        update = MockTelegramUpdate.with_inline_query(query=search_term, offset=offset)
        submission = MockSubmission(post_id)
        searchBot.api.with_search_results(search_term, [submission], page=offset)

        searchBot.inline_query(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) > 0
        for result in args[1]:
            assert isinstance(result, InlineQueryResultPhoto)
            assert result.id == str(post_id)
            assert result.photo_url == submission.thumbnail_url
            assert result.thumb_url == submission.thumbnail_url
            assert result.caption == submission.link

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_search_with_offset_no_more_results(self, bot, r):
        search_term = "YCH"
        offset = 2
        update = MockTelegramUpdate.with_inline_query(query=search_term, offset=offset)
        searchBot.api.with_search_results(search_term, [], page=offset)

        searchBot.inline_query(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == ""
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 0
