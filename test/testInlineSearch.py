import unittest

from unittest.mock import patch

import telegram
from telegram import InlineQueryResultPhoto, InlineQueryResultArticle, InputMessageContent

from bot import InlineFunctionality
from test.util.mock_export_api import MockSubmission, MockExportAPI
from test.util.testTelegramUpdateObjects import MockTelegramUpdate


class InlineSearchTest(unittest.TestCase):

    def setUp(self) -> None:
        self.inline = InlineFunctionality(MockExportAPI())

    @patch.object(telegram, "Bot")
    def test_empty_query_no_results(self, bot):
        update = MockTelegramUpdate.with_inline_query(query="")

        self.inline.call(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()
        bot.answer_inline_query.assert_called_with(update.inline_query.id, [])

    @patch.object(telegram, "Bot")
    def test_simple_search(self, bot):
        post_id = 234563
        search_term = "YCH"
        update = MockTelegramUpdate.with_inline_query(query=search_term)
        submission = MockSubmission(post_id)
        self.inline.api.with_search_results(search_term, [submission])

        self.inline.call(bot, update)

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
    def test_no_search_results(self, bot):
        search_term = "RareKeyword"
        update = MockTelegramUpdate.with_inline_query(query=search_term)
        self.inline.api.with_search_results(search_term, [])

        self.inline.call(bot, update)

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
    def test_search_with_offset(self, bot):
        post_id = 234563
        search_term = "YCH"
        offset = 2
        update = MockTelegramUpdate.with_inline_query(query=search_term, offset=offset)
        submission = MockSubmission(post_id)
        self.inline.api.with_search_results(search_term, [submission], page=offset)

        self.inline.call(bot, update)

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
    def test_search_with_offset_no_more_results(self, bot):
        search_term = "YCH"
        offset = 2
        update = MockTelegramUpdate.with_inline_query(query=search_term, offset=offset)
        self.inline.api.with_search_results(search_term, [], page=offset)

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == ""
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 0

    @patch.object(telegram, "Bot")
    def test_search_with_spaces(self, bot):
        search_term = "deer YCH"
        update = MockTelegramUpdate.with_inline_query(query=search_term)
        post_id1 = 213231
        post_id2 = 84331
        submission1 = MockSubmission(post_id1)
        submission2 = MockSubmission(post_id2)
        self.inline.api.with_search_results(search_term, [submission1, submission2])
        
        self.inline.call(bot, update)
        
        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == 2
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 2
        for result in args[1]:
            assert isinstance(result, InlineQueryResultPhoto)
        assert args[1][0].id == str(post_id1)
        assert args[1][1].id == str(post_id2)
        assert args[1][0].photo_url == submission1.thumbnail_url
        assert args[1][1].photo_url == submission2.thumbnail_url
        assert args[1][0].thumb_url == submission1.thumbnail_url
        assert args[1][1].thumb_url == submission2.thumbnail_url
        assert args[1][0].caption == submission1.link
        assert args[1][1].caption == submission2.link

    @patch.object(telegram, "Bot")
    def test_search_with_combo_characters(self, bot):
        search_term = "(deer & !ych) | (dragon & !ych)"
        update = MockTelegramUpdate.with_inline_query(query=search_term)
        post_id = 213231
        submission = MockSubmission(post_id)
        self.inline.api.with_search_results(search_term, [submission])
        
        self.inline.call(bot, update)
        
        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == 2
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultPhoto)
        assert args[1][0].id == str(post_id)
        assert args[1][0].photo_url == submission.thumbnail_url
        assert args[1][0].thumb_url == submission.thumbnail_url
        assert args[1][0].caption == submission.link

    @patch.object(telegram, "Bot")
    def test_search_with_field(self, bot):
        search_term = "@lower citrinelle"
        update = MockTelegramUpdate.with_inline_query(query=search_term)
        post_id = 213231
        submission = MockSubmission(post_id)
        self.inline.api.with_search_results(search_term, [submission])
        
        self.inline.call(bot, update)
        
        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == 2
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultPhoto)
        assert args[1][0].id == str(post_id)
        assert args[1][0].photo_url == submission.thumbnail_url
        assert args[1][0].thumb_url == submission.thumbnail_url
        assert args[1][0].caption == submission.link
