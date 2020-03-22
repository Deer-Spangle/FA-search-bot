from telegram import InlineQueryResultPhoto, InlineQueryResultArticle, InputMessageContent

from fa_export_api import FAExportAPI
from fa_submission import FASubmission
from functionalities.inline import InlineFunctionality
from tests.util.mock_export_api import MockExportAPI, MockSubmission
from tests.util.mock_telegram_update import MockTelegramUpdate


def test_user_favourites(context):
    post_id1 = 234563
    post_id2 = 393282
    username = "fender"
    update = MockTelegramUpdate.with_inline_query(query=f"favourites:{username}")
    submission1 = MockSubmission(post_id1)
    submission2 = MockSubmission(post_id2)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [submission1, submission2])

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == submission2.fav_id
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 2
    assert isinstance(args[1][0], InlineQueryResultPhoto)
    assert isinstance(args[1][1], InlineQueryResultPhoto)
    assert args[1][0].id == str(post_id1)
    assert args[1][1].id == str(post_id2)
    assert args[1][0].photo_url == submission1.thumbnail_url
    assert args[1][1].photo_url == submission2.thumbnail_url
    assert args[1][0].thumb_url == FASubmission.make_thumbnail_smaller(submission1.thumbnail_url)
    assert args[1][1].thumb_url == FASubmission.make_thumbnail_smaller(submission2.thumbnail_url)
    assert args[1][0].caption == submission1.link
    assert args[1][1].caption == submission2.link


def test_user_favs(context):
    post_id = 234563
    username = "citrinelle"
    update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [submission])

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == submission.fav_id
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 1
    assert isinstance(args[1][0], InlineQueryResultPhoto)
    assert args[1][0].id == str(post_id)
    assert args[1][0].photo_url == submission.thumbnail_url
    assert args[1][0].thumb_url == FASubmission.make_thumbnail_smaller(submission.thumbnail_url)
    assert args[1][0].caption == submission.link


def test_american_spelling(context):
    post_id = 234563
    username = "citrinelle"
    update = MockTelegramUpdate.with_inline_query(query=f"favorites:{username}")
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [submission])

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == submission.fav_id
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 1
    assert isinstance(args[1][0], InlineQueryResultPhoto)
    assert args[1][0].id == str(post_id)
    assert args[1][0].photo_url == submission.thumbnail_url
    assert args[1][0].thumb_url == FASubmission.make_thumbnail_smaller(submission.thumbnail_url)
    assert args[1][0].caption == submission.link


def test_continue_from_fav_id(context):
    post_id = 234563
    fav_id = "354233"
    username = "citrinelle"
    update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}", offset=fav_id)
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [submission], next_id=fav_id)

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == submission.fav_id
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 1
    assert isinstance(args[1][0], InlineQueryResultPhoto)
    assert args[1][0].id == str(post_id)
    assert args[1][0].photo_url == submission.thumbnail_url
    assert args[1][0].thumb_url == FASubmission.make_thumbnail_smaller(submission.thumbnail_url)
    assert args[1][0].caption == submission.link


def test_empty_favs(context):
    username = "fender"
    update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [])

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == ""
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 1
    assert isinstance(args[1][0], InlineQueryResultArticle)
    assert args[1][0].title == "Nothing in favourites."
    assert isinstance(args[1][0].input_message_content, InputMessageContent)
    assert args[1][0].input_message_content.message_text == \
           f"There are no favourites for user \"{username}\"."


def test_hypens_in_username(context):
    post_id = 234563
    username = "dr-spangle"
    update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [submission])

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == submission.fav_id
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 1
    assert isinstance(args[1][0], InlineQueryResultPhoto)
    assert args[1][0].id == str(post_id)
    assert args[1][0].photo_url == submission.thumbnail_url
    assert args[1][0].thumb_url == FASubmission.make_thumbnail_smaller(submission.thumbnail_url)
    assert args[1][0].caption == submission.link


def test_weird_characters_in_username(context):
    post_id = 234563
    username = "l[i]s"
    update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [submission])

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == submission.fav_id
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 1
    assert isinstance(args[1][0], InlineQueryResultPhoto)
    assert args[1][0].id == str(post_id)
    assert args[1][0].photo_url == submission.thumbnail_url
    assert args[1][0].thumb_url == FASubmission.make_thumbnail_smaller(submission.thumbnail_url)
    assert args[1][0].caption == submission.link


def test_no_user_exists(context, requests_mock):
    username = "fakelad"
    update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")
    inline = InlineFunctionality(MockExportAPI())
    # mock export api doesn't do non-existent users, so mocking with requests
    inline.api = FAExportAPI("http://example.com")
    requests_mock.get(
        f"http://example.com/user/{username}/favorites.json",
        status_code=404
    )

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == ""
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 1
    assert isinstance(args[1][0], InlineQueryResultArticle)
    assert args[1][0].title == "User does not exist."
    assert isinstance(args[1][0].input_message_content, InputMessageContent)
    assert args[1][0].input_message_content.message_text == \
           f"FurAffinity user does not exist by the name: \"{username}\"."


def test_username_with_colon(context, requests_mock):
    # FA doesn't allow usernames to have : in them
    username = "fake:lad"
    update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")
    inline = InlineFunctionality(MockExportAPI())
    # mock export api doesn't do non-existent users, so mocking with requests
    inline.api = FAExportAPI("http://example.com")
    requests_mock.get(
        f"http://example.com/user/{username}/favorites.json",
        status_code=404
    )

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == ""
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 1
    assert isinstance(args[1][0], InlineQueryResultArticle)
    assert args[1][0].title == "User does not exist."
    assert isinstance(args[1][0].input_message_content, InputMessageContent)
    assert args[1][0].input_message_content.message_text == \
           f"FurAffinity user does not exist by the name: \"{username}\"."


def test_over_48_favs(context):
    username = "citrinelle"
    post_ids = list(range(123456, 123456 + 72))
    submissions = [MockSubmission(x) for x in post_ids]
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, submissions)
    update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == submissions[47].fav_id
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 48
    assert isinstance(args[1][0], InlineQueryResultPhoto)
    assert isinstance(args[1][1], InlineQueryResultPhoto)
    for x in range(48):
        assert args[1][x].id == str(post_ids[x])
        assert args[1][x].photo_url == submissions[x].thumbnail_url
        assert args[1][x].thumb_url == FASubmission.make_thumbnail_smaller(submissions[x].thumbnail_url)
        assert args[1][x].caption == submissions[x].link


def test_no_username_set(context, requests_mock):
    username = ""
    update = MockTelegramUpdate.with_inline_query(query=f"favs:{username}")
    inline = InlineFunctionality(MockExportAPI())
    # mock export api doesn't do non-existent users, so mocking with requests
    inline.api = FAExportAPI("http://example.com")
    requests_mock.get(
        f"http://example.com/user/{username}/favorites.json?page=1&full=1",
        json={
            "id": None,
            "name": "favorites",
            "profile": "https://www.furaffinity.net/user/favorites/"
        }
    )

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == ""
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 1
    assert isinstance(args[1][0], InlineQueryResultArticle)
    assert args[1][0].title == "User does not exist."
    assert isinstance(args[1][0].input_message_content, InputMessageContent)
    assert args[1][0].input_message_content.message_text == \
           f"FurAffinity user does not exist by the name: \"{username}\"."


def test_user_favourites_last_page(context):
    # On the last page of favourites, if you specify "next", it repeats the same page, this simulates that.
    post_id1 = 234563
    post_id2 = 393282
    submission1 = MockSubmission(post_id1)
    submission2 = MockSubmission(post_id2)
    username = "fender"
    update = MockTelegramUpdate.with_inline_query(query=f"favourites:{username}", offset=submission2.fav_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [submission1, submission2], next_id=submission2.fav_id)

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == ""
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 0
