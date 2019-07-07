import unittest

from unittest.mock import patch

import requests_mock
import telegram
from telegram import InlineQueryResultPhoto, InlineQueryResultArticle, InputMessageContent

from bot import InlineFunctionality
from fa_export_api import FAExportAPI
from tests.util.mock_export_api import MockSubmission, MockExportAPI
from tests.util.mock_telegram_update import MockTelegramUpdate


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


class InlineUserGalleryTest(unittest.TestCase):

    def setUp(self) -> None:
        self.inline = InlineFunctionality(MockExportAPI())

    @patch.object(telegram, "Bot")
    def test_get_user_gallery(self, bot):
        post_id1 = 234563
        post_id2 = 393282
        username = "fender"
        update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")
        submission1 = MockSubmission(post_id1)
        submission2 = MockSubmission(post_id2)
        self.inline.api.with_user_folder(username, "gallery", [submission1, submission2])

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == 2
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 2
        assert isinstance(args[1][0], InlineQueryResultPhoto)
        assert isinstance(args[1][1], InlineQueryResultPhoto)
        assert args[1][0].id == str(post_id1)
        assert args[1][1].id == str(post_id2)
        assert args[1][0].photo_url == submission1.thumbnail_url
        assert args[1][1].photo_url == submission2.thumbnail_url
        assert args[1][0].thumb_url == submission1.thumbnail_url
        assert args[1][1].thumb_url == submission2.thumbnail_url
        assert args[1][0].caption == submission1.link
        assert args[1][1].caption == submission2.link

    @patch.object(telegram, "Bot")
    def test_user_scraps(self, bot):
        post_id = 234563
        username = "citrinelle"
        update = MockTelegramUpdate.with_inline_query(query=f"scraps:{username}")
        submission = MockSubmission(post_id)
        self.inline.api.with_user_folder(username, "scraps", [submission])

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
    def test_second_page(self, bot):
        post_id = 234563
        username = "citrinelle"
        update = MockTelegramUpdate.with_inline_query(query=f"scraps:{username}", offset="2")
        submission = MockSubmission(post_id)
        self.inline.api.with_user_folder(username, "scraps", [submission], page=2)

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == 3
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultPhoto)
        assert args[1][0].id == str(post_id)
        assert args[1][0].photo_url == submission.thumbnail_url
        assert args[1][0].thumb_url == submission.thumbnail_url
        assert args[1][0].caption == submission.link

    @patch.object(telegram, "Bot")
    def test_empty_gallery(self, bot):
        username = "fender"
        update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")
        self.inline.api.with_user_folder(username, "gallery", [])

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == ""
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultArticle)
        assert args[1][0].title == "Nothing in gallery."
        assert isinstance(args[1][0].input_message_content, InputMessageContent)
        assert args[1][0].input_message_content.message_text == \
            f"There are no submissions in gallery for user \"{username}\"."

    @patch.object(telegram, "Bot")
    def test_empty_scraps(self, bot):
        username = "fender"
        update = MockTelegramUpdate.with_inline_query(query=f"scraps:{username}")
        self.inline.api.with_user_folder(username, "scraps", [])

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == ""
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultArticle)
        assert args[1][0].title == "Nothing in scraps."
        assert isinstance(args[1][0].input_message_content, InputMessageContent)
        assert args[1][0].input_message_content.message_text == \
            f"There are no submissions in scraps for user \"{username}\"."

    @patch.object(telegram, "Bot")
    def test_hypens_in_username(self, bot):
        post_id = 234563
        username = "dr-spangle"
        update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")
        submission = MockSubmission(post_id)
        self.inline.api.with_user_folder(username, "gallery", [submission])

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
    def test_weird_characters_in_username(self, bot):
        post_id = 234563
        username = "l[i]s"
        update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")
        submission = MockSubmission(post_id)
        self.inline.api.with_user_folder(username, "gallery", [submission])

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
    @requests_mock.mock()
    def test_no_user_exists(self, bot, r):
        username = "fakelad"
        update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")
        # mock export api doesn't do non-existent users, so mocking with requests
        self.inline.api = FAExportAPI("http://example.com")
        r.get(
            f"http://example.com/user/{username}/gallery.json",
            status_code=404
        )

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == ""
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultArticle)
        assert args[1][0].title == "User does not exist."
        assert isinstance(args[1][0].input_message_content, InputMessageContent)
        assert args[1][0].input_message_content.message_text == \
            f"FurAffinity user does not exist by the name: \"{username}\"."

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_username_with_colon(self, bot, r):
        # FA doesn't allow usernames to have : in them
        username = "fake:lad"
        update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")
        # mock export api doesn't do non-existent users, so mocking with requests
        self.inline.api = FAExportAPI("http://example.com")
        r.get(
            f"http://example.com/user/{username}/gallery.json",
            status_code=404
        )

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == ""
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultArticle)
        assert args[1][0].title == "User does not exist."
        assert isinstance(args[1][0].input_message_content, InputMessageContent)
        assert args[1][0].input_message_content.message_text == \
            f"FurAffinity user does not exist by the name: \"{username}\"."

    @patch.object(telegram, "Bot")
    def test_over_48_submissions(self, bot):
        username = "citrinelle"
        post_ids = list(range(123456, 123456+72))
        submissions = [MockSubmission(x) for x in post_ids]
        self.inline.api.with_user_folder(username, "gallery", submissions)
        update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == "1:48"
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 48
        assert isinstance(args[1][0], InlineQueryResultPhoto)
        assert isinstance(args[1][1], InlineQueryResultPhoto)
        for x in range(48):
            assert args[1][x].id == str(post_ids[x])
            assert args[1][x].photo_url == submissions[x].thumbnail_url
            assert args[1][x].thumb_url == submissions[x].thumbnail_url
            assert args[1][x].caption == submissions[x].link

    @patch.object(telegram, "Bot")
    def test_over_48_submissions_continue(self, bot):
        username = "citrinelle"
        post_ids = list(range(123456, 123456+72))
        submissions = [MockSubmission(x) for x in post_ids]
        self.inline.api.with_user_folder(username, "gallery", submissions)
        update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}", offset="1:48")

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == 2
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 72-48
        assert isinstance(args[1][0], InlineQueryResultPhoto)
        assert isinstance(args[1][1], InlineQueryResultPhoto)
        for x in range(72-48):
            assert args[1][x].id == str(post_ids[x+48])
            assert args[1][x].photo_url == submissions[x+48].thumbnail_url
            assert args[1][x].thumb_url == submissions[x+48].thumbnail_url
            assert args[1][x].caption == submissions[x+48].link

    @patch.object(telegram, "Bot")
    def test_over_48_submissions_continue_weird(self, bot):
        username = "citrinelle"
        post_ids = list(range(123456, 123456+72))
        skip = 37
        submissions = [MockSubmission(x) for x in post_ids]
        self.inline.api.with_user_folder(username, "gallery", submissions)
        update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}", offset=f"1:{skip}")

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == 2
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 72-skip
        assert isinstance(args[1][0], InlineQueryResultPhoto)
        assert isinstance(args[1][1], InlineQueryResultPhoto)
        for x in range(72-skip):
            assert args[1][x].id == str(post_ids[x+skip])
            assert args[1][x].photo_url == submissions[x+skip].thumbnail_url
            assert args[1][x].thumb_url == submissions[x+skip].thumbnail_url
            assert args[1][x].caption == submissions[x+skip].link

    @patch.object(telegram, "Bot")
    def test_double_48_submissions_continue(self, bot):
        username = "citrinelle"
        post_ids = list(range(123456, 123456+150))
        submissions = [MockSubmission(x) for x in post_ids]
        self.inline.api.with_user_folder(username, "gallery", submissions)
        update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}", offset="1:48")

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == "1:96"
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 48
        assert isinstance(args[1][0], InlineQueryResultPhoto)
        assert isinstance(args[1][1], InlineQueryResultPhoto)
        for x in range(48):
            assert args[1][x].id == str(post_ids[x+48])
            assert args[1][x].photo_url == submissions[x+48].thumbnail_url
            assert args[1][x].thumb_url == submissions[x+48].thumbnail_url
            assert args[1][x].caption == submissions[x+48].link

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_no_username_set(self, bot, r):
        username = ""
        update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")
        # mock export api doesn't do non-existent users, so mocking with requests
        self.inline.api = FAExportAPI("http://example.com")
        r.get(
            f"http://example.com/user/{username}/gallery.json?page=1&full=1",
            json={
                "id": None,
                "name": "gallery",
                "profile": "https://www.furaffinity.net/user/gallery/"
            }
        )

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == ""
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultArticle)
        assert args[1][0].title == "User does not exist."
        assert isinstance(args[1][0].input_message_content, InputMessageContent)
        assert args[1][0].input_message_content.message_text == \
            f"FurAffinity user does not exist by the name: \"{username}\"."


class InlineUserFavouritesTest(unittest.TestCase):

    def setUp(self) -> None:
        self.inline = InlineFunctionality(MockExportAPI())

    @patch.object(telegram, "Bot")
    def test_user_favourites(self, bot):
        post_id1 = 234563
        post_id2 = 393282
        username = "fender"
        update = MockTelegramUpdate.with_inline_query(query=f"favourites:{username}")
        submission1 = MockSubmission(post_id1)
        submission2 = MockSubmission(post_id2)
        self.inline.api.with_user_favs(username, [submission1, submission2])

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == submission2.fav_id
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 2
        assert isinstance(args[1][0], InlineQueryResultPhoto)
        assert isinstance(args[1][1], InlineQueryResultPhoto)
        assert args[1][0].id == str(post_id1)
        assert args[1][1].id == str(post_id2)
        assert args[1][0].photo_url == submission1.thumbnail_url
        assert args[1][1].photo_url == submission2.thumbnail_url
        assert args[1][0].thumb_url == submission1.thumbnail_url
        assert args[1][1].thumb_url == submission2.thumbnail_url
        assert args[1][0].caption == submission1.link
        assert args[1][1].caption == submission2.link

    @patch.object(telegram, "Bot")
    def test_user_favs(self, bot):
        post_id = 234563
        username = "citrinelle"
        update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")
        submission = MockSubmission(post_id)
        self.inline.api.with_user_favs(username, [submission])

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == submission.fav_id
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultPhoto)
        assert args[1][0].id == str(post_id)
        assert args[1][0].photo_url == submission.thumbnail_url
        assert args[1][0].thumb_url == submission.thumbnail_url
        assert args[1][0].caption == submission.link

    @patch.object(telegram, "Bot")
    def test_american_spelling(self, bot):
        post_id = 234563
        username = "citrinelle"
        update = MockTelegramUpdate.with_inline_query(query=f"favorites:{username}")
        submission = MockSubmission(post_id)
        self.inline.api.with_user_favs(username, [submission])

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == submission.fav_id
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultPhoto)
        assert args[1][0].id == str(post_id)
        assert args[1][0].photo_url == submission.thumbnail_url
        assert args[1][0].thumb_url == submission.thumbnail_url
        assert args[1][0].caption == submission.link

    @patch.object(telegram, "Bot")
    def test_continue_from_fav_id(self, bot):
        post_id = 234563
        fav_id = "354233"
        username = "citrinelle"
        update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}", offset=fav_id)
        submission = MockSubmission(post_id)
        self.inline.api.with_user_favs(username, [submission], next_id=fav_id)

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == submission.fav_id
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultPhoto)
        assert args[1][0].id == str(post_id)
        assert args[1][0].photo_url == submission.thumbnail_url
        assert args[1][0].thumb_url == submission.thumbnail_url
        assert args[1][0].caption == submission.link

    @patch.object(telegram, "Bot")
    def test_empty_favs(self, bot):
        username = "fender"
        update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")
        self.inline.api.with_user_favs(username, [])

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == ""
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultArticle)
        assert args[1][0].title == "Nothing in favourites."
        assert isinstance(args[1][0].input_message_content, InputMessageContent)
        assert args[1][0].input_message_content.message_text == \
            f"There are no favourites for user \"{username}\"."

    @patch.object(telegram, "Bot")
    def test_hypens_in_username(self, bot):
        post_id = 234563
        username = "dr-spangle"
        update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")
        submission = MockSubmission(post_id)
        self.inline.api.with_user_favs(username, [submission])

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == submission.fav_id
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultPhoto)
        assert args[1][0].id == str(post_id)
        assert args[1][0].photo_url == submission.thumbnail_url
        assert args[1][0].thumb_url == submission.thumbnail_url
        assert args[1][0].caption == submission.link

    @patch.object(telegram, "Bot")
    def test_weird_characters_in_username(self, bot):
        post_id = 234563
        username = "l[i]s"
        update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")
        submission = MockSubmission(post_id)
        self.inline.api.with_user_favs(username, [submission])

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == submission.fav_id
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultPhoto)
        assert args[1][0].id == str(post_id)
        assert args[1][0].photo_url == submission.thumbnail_url
        assert args[1][0].thumb_url == submission.thumbnail_url
        assert args[1][0].caption == submission.link

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_no_user_exists(self, bot, r):
        username = "fakelad"
        update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")
        # mock export api doesn't do non-existent users, so mocking with requests
        self.inline.api = FAExportAPI("http://example.com")
        r.get(
            f"http://example.com/user/{username}/favorites.json",
            status_code=404
        )

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == ""
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultArticle)
        assert args[1][0].title == "User does not exist."
        assert isinstance(args[1][0].input_message_content, InputMessageContent)
        assert args[1][0].input_message_content.message_text == \
            f"FurAffinity user does not exist by the name: \"{username}\"."

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_username_with_colon(self, bot, r):
        # FA doesn't allow usernames to have : in them
        username = "fake:lad"
        update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")
        # mock export api doesn't do non-existent users, so mocking with requests
        self.inline.api = FAExportAPI("http://example.com")
        r.get(
            f"http://example.com/user/{username}/favorites.json",
            status_code=404
        )

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == ""
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultArticle)
        assert args[1][0].title == "User does not exist."
        assert isinstance(args[1][0].input_message_content, InputMessageContent)
        assert args[1][0].input_message_content.message_text == \
            f"FurAffinity user does not exist by the name: \"{username}\"."

    @patch.object(telegram, "Bot")
    def test_over_48_favs(self, bot):
        username = "citrinelle"
        post_ids = list(range(123456, 123456+72))
        submissions = [MockSubmission(x) for x in post_ids]
        self.inline.api.with_user_favs(username, submissions)
        update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == submissions[47].fav_id
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 48
        assert isinstance(args[1][0], InlineQueryResultPhoto)
        assert isinstance(args[1][1], InlineQueryResultPhoto)
        for x in range(48):
            assert args[1][x].id == str(post_ids[x])
            assert args[1][x].photo_url == submissions[x].thumbnail_url
            assert args[1][x].thumb_url == submissions[x].thumbnail_url
            assert args[1][x].caption == submissions[x].link

    @patch.object(telegram, "Bot")
    @requests_mock.mock()
    def test_no_username_set(self, bot, r):
        username = ""
        update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")
        # mock export api doesn't do non-existent users, so mocking with requests
        self.inline.api = FAExportAPI("http://example.com")
        r.get(
            f"http://example.com/user/{username}/favorites.json?page=1&full=1",
            json={
                "id": None,
                "name": "favorites",
                "profile": "https://www.furaffinity.net/user/favorites/"
            }
        )

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == ""
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 1
        assert isinstance(args[1][0], InlineQueryResultArticle)
        assert args[1][0].title == "User does not exist."
        assert isinstance(args[1][0].input_message_content, InputMessageContent)
        assert args[1][0].input_message_content.message_text == \
            f"FurAffinity user does not exist by the name: \"{username}\"."

    @patch.object(telegram, "Bot")
    def test_user_favourites_last_page(self, bot):
        # On the last page of favourites, if you specify "next", it repeats the same page, this simulates that.
        post_id1 = 234563
        post_id2 = 393282
        username = "fender"
        update = MockTelegramUpdate.with_inline_query(query=f"favourites:{username}")
        submission1 = MockSubmission(post_id1)
        submission2 = MockSubmission(post_id2)
        self.inline.api.with_user_favs(username, [submission1, submission2], next_id=submission2.fav_id)

        self.inline.call(bot, update)

        bot.answer_inline_query.assert_called_once()
        args = bot.answer_inline_query.call_args[0]
        assert bot.answer_inline_query.call_args[1]['next_offset'] == ""
        assert args[0] == update.inline_query.id
        assert isinstance(args[1], list)
        assert len(args[1]) == 0
