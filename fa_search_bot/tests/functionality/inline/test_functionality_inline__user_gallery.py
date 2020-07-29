from telegram import InlineQueryResultPhoto, InlineQueryResultArticle, InputMessageContent

from fa_search_bot.fa_export_api import FAExportAPI
from fa_search_bot.fa_submission import FASubmission
from fa_search_bot.functionalities.inline import InlineFunctionality
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_telegram_update import MockTelegramUpdate


def test_get_user_gallery(context):
    post_id1 = 234563
    post_id2 = 393282
    username = "fender"
    update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")
    submission1 = MockSubmission(post_id1)
    submission2 = MockSubmission(post_id2)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_folder(username, "gallery", [submission1, submission2])

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == 2
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


def test_user_scraps(context):
    post_id = 234563
    username = "citrinelle"
    update = MockTelegramUpdate.with_inline_query(query=f"scraps:{username}")
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_folder(username, "scraps", [submission])

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == 2
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 1
    assert isinstance(args[1][0], InlineQueryResultPhoto)
    assert args[1][0].id == str(post_id)
    assert args[1][0].photo_url == submission.thumbnail_url
    assert args[1][0].thumb_url == FASubmission.make_thumbnail_smaller(submission.thumbnail_url)
    assert args[1][0].caption == submission.link


def test_second_page(context):
    post_id = 234563
    username = "citrinelle"
    update = MockTelegramUpdate.with_inline_query(query=f"scraps:{username}", offset="2")
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_folder(username, "scraps", [submission], page=2)

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == 3
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 1
    assert isinstance(args[1][0], InlineQueryResultPhoto)
    assert args[1][0].id == str(post_id)
    assert args[1][0].photo_url == submission.thumbnail_url
    assert args[1][0].thumb_url == FASubmission.make_thumbnail_smaller(submission.thumbnail_url)
    assert args[1][0].caption == submission.link


def test_empty_gallery(context):
    username = "fender"
    update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_folder(username, "gallery", [])

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == ""
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 1
    assert isinstance(args[1][0], InlineQueryResultArticle)
    assert args[1][0].title == "Nothing in gallery."
    assert isinstance(args[1][0].input_message_content, InputMessageContent)
    assert args[1][0].input_message_content.message_text == \
           f"There are no submissions in gallery for user \"{username}\"."


def test_empty_scraps(context):
    username = "fender"
    update = MockTelegramUpdate.with_inline_query(query=f"scraps:{username}")
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_folder(username, "scraps", [])

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == ""
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 1
    assert isinstance(args[1][0], InlineQueryResultArticle)
    assert args[1][0].title == "Nothing in scraps."
    assert isinstance(args[1][0].input_message_content, InputMessageContent)
    assert args[1][0].input_message_content.message_text == \
           f"There are no submissions in scraps for user \"{username}\"."


def test_hypens_in_username(context):
    post_id = 234563
    username = "dr-spangle"
    update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_folder(username, "gallery", [submission])

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == 2
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
    update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_folder(username, "gallery", [submission])

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == 2
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
    update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")
    inline = InlineFunctionality(MockExportAPI())
    # mock export api doesn't do non-existent users, so mocking with requests
    inline.api = FAExportAPI("http://example.com")
    requests_mock.get(
        f"http://example.com/user/{username}/gallery.json",
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
    update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")
    inline = InlineFunctionality(MockExportAPI())
    # mock export api doesn't do non-existent users, so mocking with requests
    inline.api = FAExportAPI("http://example.com")
    requests_mock.get(
        f"http://example.com/user/{username}/gallery.json",
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


def test_over_48_submissions(context):
    username = "citrinelle"
    post_ids = list(range(123456, 123456 + 72))
    submissions = [MockSubmission(x) for x in post_ids]
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_folder(username, "gallery", submissions)
    update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == "1:48"
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


def test_over_48_submissions_continue(context):
    username = "citrinelle"
    post_ids = list(range(123456, 123456 + 72))
    submissions = [MockSubmission(x) for x in post_ids]
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_folder(username, "gallery", submissions)
    update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}", offset="1:48")

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == 2
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 72 - 48
    assert isinstance(args[1][0], InlineQueryResultPhoto)
    assert isinstance(args[1][1], InlineQueryResultPhoto)
    for x in range(72 - 48):
        assert args[1][x].id == str(post_ids[x + 48])
        assert args[1][x].photo_url == submissions[x + 48].thumbnail_url
        assert args[1][x].thumb_url == FASubmission.make_thumbnail_smaller(submissions[x + 48].thumbnail_url)
        assert args[1][x].caption == submissions[x + 48].link


def test_over_48_submissions_continue_weird(context):
    username = "citrinelle"
    post_ids = list(range(123456, 123456 + 72))
    skip = 37
    submissions = [MockSubmission(x) for x in post_ids]
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_folder(username, "gallery", submissions)
    update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}", offset=f"1:{skip}")

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == 2
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 72 - skip
    assert isinstance(args[1][0], InlineQueryResultPhoto)
    assert isinstance(args[1][1], InlineQueryResultPhoto)
    for x in range(72 - skip):
        assert args[1][x].id == str(post_ids[x + skip])
        assert args[1][x].photo_url == submissions[x + skip].thumbnail_url
        assert args[1][x].thumb_url == FASubmission.make_thumbnail_smaller(submissions[x + skip].thumbnail_url)
        assert args[1][x].caption == submissions[x + skip].link


def test_double_48_submissions_continue(context):
    username = "citrinelle"
    post_ids = list(range(123456, 123456 + 150))
    submissions = [MockSubmission(x) for x in post_ids]
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_folder(username, "gallery", submissions)
    update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}", offset="1:48")

    inline.call(update, context)

    context.bot.answer_inline_query.assert_called_once()
    args = context.bot.answer_inline_query.call_args[0]
    assert context.bot.answer_inline_query.call_args[1]['next_offset'] == "1:96"
    assert args[0] == update.inline_query.id
    assert isinstance(args[1], list)
    assert len(args[1]) == 48
    assert isinstance(args[1][0], InlineQueryResultPhoto)
    assert isinstance(args[1][1], InlineQueryResultPhoto)
    for x in range(48):
        assert args[1][x].id == str(post_ids[x + 48])
        assert args[1][x].photo_url == submissions[x + 48].thumbnail_url
        assert args[1][x].thumb_url == FASubmission.make_thumbnail_smaller(submissions[x + 48].thumbnail_url)
        assert args[1][x].caption == submissions[x + 48].link


def test_no_username_set(context, requests_mock):
    username = ""
    update = MockTelegramUpdate.with_inline_query(query=f"gallery:{username}")
    inline = InlineFunctionality(MockExportAPI())
    # mock export api doesn't do non-existent users, so mocking with requests
    inline.api = FAExportAPI("http://example.com")
    requests_mock.get(
        f"http://example.com/user/{username}/gallery.json?page=1&full=1",
        json={
            "id": None,
            "name": "gallery",
            "profile": "https://www.furaffinity.net/user/gallery/"
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
