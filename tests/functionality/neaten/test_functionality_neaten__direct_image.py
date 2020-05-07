from unittest.mock import call

from telegram import Chat

from functionalities.neaten import NeatenFunctionality
from tests.util.mock_export_api import MockExportAPI, MockSubmission
from tests.util.mock_telegram_update import MockTelegramUpdate


def test_ignore_message(context):
    update = MockTelegramUpdate.with_message(text="hello world")
    neaten = NeatenFunctionality(MockExportAPI())

    neaten.call(update, context)

    context.bot.send_message.assert_not_called()
    context.bot.send_photo.assert_not_called()


def test_ignore_link(context):
    update = MockTelegramUpdate.with_message(text="http://example.com")
    neaten = NeatenFunctionality(MockExportAPI())

    neaten.call(update, context)

    context.bot.send_message.assert_not_called()
    context.bot.send_photo.assert_not_called()


def test_ignore_profile_link(context):
    update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/user/fender/")
    neaten = NeatenFunctionality(MockExportAPI())

    neaten.call(update, context)

    context.bot.send_message.assert_not_called()
    context.bot.send_photo.assert_not_called()


def test_ignore_journal_link(context):
    update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/journal/9150534/")
    neaten = NeatenFunctionality(MockExportAPI())

    neaten.call(update, context)

    context.bot.send_message.assert_not_called()
    context.bot.send_photo.assert_not_called()


def test_direct_link(context):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    goal_submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        goal_submission,
        MockSubmission(post_id - 1, image_id=image_id - 15)
    ])

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == goal_submission.download_url
    assert context.bot.send_photo.call_args[1]['caption'] == goal_submission.link
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_direct_no_match(context):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    neaten = NeatenFunctionality(MockExportAPI())
    for folder in ['gallery', 'scraps']:
        neaten.api.with_user_folder(username, folder, [
            MockSubmission(post_id, image_id=image_id + 4),
            MockSubmission(post_id - 1, image_id=image_id - 15)
        ])

    neaten.call(update, context)

    context.bot.send_photo.assert_not_called()
    context.bot.send_message.assert_called()
    context.bot.send_message.assert_called_with(
        chat_id=update.message.chat_id,
        text="Could not locate the image by {} with image id {}.".format(username, image_id),
        reply_to_message_id=update.message.message_id
    )


def test_direct_no_match_groupchat(context):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id),
        chat_type=Chat.GROUP
    )
    neaten = NeatenFunctionality(MockExportAPI())
    for folder in ['gallery', 'scraps']:
        neaten.api.with_user_folder(username, folder, [
            MockSubmission(post_id, image_id=image_id + 4),
            MockSubmission(post_id - 1, image_id=image_id - 15)
        ])

    neaten.call(update, context)

    context.bot.send_photo.assert_not_called()
    context.bot.send_message.assert_not_called()


def test_two_direct_links(context):
    username = "fender"
    image_id1 = 1560331512
    image_id2 = 1560331510
    post_id1 = 232347
    post_id2 = 232346
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png "
             "http://d.facdn.net/art/{0}/{2}/{2}.pic_of_you.png".format(username, image_id1, image_id2)
    )
    submission1 = MockSubmission(post_id1, image_id=image_id1)
    submission2 = MockSubmission(post_id2, image_id=image_id2)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        submission1,
        submission2,
        MockSubmission(post_id2 - 1, image_id=image_id2 - 15)
    ])

    neaten.call(update, context)

    context.bot.send_photo.assert_called()
    calls = [call(
        chat_id=update.message.chat_id,
        photo=submission.download_url,
        caption=submission.link,
        reply_to_message_id=update.message.message_id
    ) for submission in [submission1, submission2]]
    context.bot.send_photo.assert_has_calls(calls)


def test_duplicate_direct_link(context):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png ".format(username, image_id) * 2
    )
    submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        submission,
        MockSubmission(post_id - 1, image_id=image_id - 15)
    ])

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.download_url
    assert context.bot.send_photo.call_args[1]['caption'] == submission.link
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_direct_link_and_matching_submission_link(context):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png https://furaffinity.net/view/{2}/".format(
            username, image_id, post_id
        )
    )
    submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        submission,
        MockSubmission(post_id - 1, image_id=image_id - 15)
    ])

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.download_url
    assert context.bot.send_photo.call_args[1]['caption'] == submission.link
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_direct_link_and_different_submission_link(context):
    username = "fender"
    image_id1 = 1560331512
    image_id2 = image_id1 + 300
    post_id1 = 232347
    post_id2 = 233447
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png https://furaffinity.net/view/{2}/".format(
            username, image_id1, post_id2
        )
    )
    submission1 = MockSubmission(post_id1, image_id=image_id1)
    submission2 = MockSubmission(post_id2, image_id=image_id2)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        submission2,
        submission1,
        MockSubmission(post_id1 - 1, image_id=image_id1 - 15)
    ])

    neaten.call(update, context)

    context.bot.send_photo.assert_called()
    calls = [call(
        chat_id=update.message.chat_id,
        photo=submission.download_url,
        caption=submission.link,
        reply_to_message_id=update.message.message_id
    ) for submission in [submission1, submission2]]
    context.bot.send_photo.assert_has_calls(calls)


def test_submission_link_and_different_direct_link(context):
    username = "fender"
    image_id1 = 1560331512
    image_id2 = image_id1 + 300
    post_id1 = 232347
    post_id2 = 233447
    update = MockTelegramUpdate.with_message(
        text="https://furaffinity.net/view/{2}/ http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(
            username, image_id1, post_id2
        )
    )
    submission1 = MockSubmission(post_id1, image_id=image_id1)
    submission2 = MockSubmission(post_id2, image_id=image_id2)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        submission2,
        submission1,
        MockSubmission(post_id1 - 1, image_id=image_id1 - 15)
    ])

    neaten.call(update, context)

    context.bot.send_photo.assert_called()
    calls = [call(
        chat_id=update.message.chat_id,
        photo=submission.download_url,
        caption=submission.link,
        reply_to_message_id=update.message.message_id
    ) for submission in [submission2, submission1]]
    context.bot.send_photo.assert_has_calls(calls)


def test_result_on_first_page(context):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        MockSubmission(post_id + 1, image_id=image_id + 16),
        submission,
        MockSubmission(post_id - 2, image_id=image_id - 27),
        MockSubmission(post_id - 3, image_id=image_id - 34)
    ])

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.download_url
    assert context.bot.send_photo.call_args[1]['caption'] == submission.link
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_result_on_third_page(context):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    neaten = NeatenFunctionality(MockExportAPI())
    for page in [1, 2, 3]:
        neaten.api.with_user_folder(username, "gallery", [
            MockSubmission(post_id + 1 + (3 - page) * 5, image_id=image_id + 16 + (3 - page) * 56),
            MockSubmission(post_id + (3 - page) * 5, image_id=image_id + (3 - page) * 56),
            MockSubmission(post_id - 2 + (3 - page) * 5, image_id=image_id - 27 + (3 - page) * 56),
            MockSubmission(post_id - 3 + (3 - page) * 5, image_id=image_id - 34 + (3 - page) * 56)
        ], page=page)
    submission = neaten.api.get_full_submission(str(post_id))

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.download_url
    assert context.bot.send_photo.call_args[1]['caption'] == submission.link
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_result_missing_from_first_page(context):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        MockSubmission(post_id + 1, image_id=image_id + 16),
        MockSubmission(post_id, image_id=image_id + 3),
        MockSubmission(post_id - 2, image_id=image_id - 27),
        MockSubmission(post_id - 3, image_id=image_id - 34)
    ])

    neaten.call(update, context)

    context.bot.send_photo.assert_not_called()
    context.bot.send_message.assert_called_once()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_message.call_args[1]['text'] == \
           "Could not locate the image by {} with image id {}.".format(username, image_id)
    assert context.bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_result_missing_from_second_page(context):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    neaten = NeatenFunctionality(MockExportAPI())
    for page in [1, 2]:
        neaten.api.with_user_folder(username, "gallery", [
            MockSubmission(post_id + 1 + (2 - page) * 6, image_id=image_id + 16 + (2 - page) * 56),
            MockSubmission(post_id + 0 + (2 - page) * 6, image_id=image_id + 3 + (2 - page) * 56),
            MockSubmission(post_id - 2 + (2 - page) * 6, image_id=image_id - 27 + (2 - page) * 56),
            MockSubmission(post_id - 3 + (2 - page) * 6, image_id=image_id - 34 + (2 - page) * 56)
        ], page=page)

    neaten.call(update, context)

    context.bot.send_photo.assert_not_called()
    context.bot.send_message.assert_called_once()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_message.call_args[1]['text'] == \
           "Could not locate the image by {} with image id {}.".format(username, image_id)
    assert context.bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_result_missing_between_pages(context):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        MockSubmission(post_id + 1, image_id=image_id + 16),
        MockSubmission(post_id, image_id=image_id + 3)
    ], page=1)
    neaten.api.with_user_folder(username, "gallery", [
        MockSubmission(post_id - 2, image_id=image_id - 27),
        MockSubmission(post_id - 3, image_id=image_id - 34)
    ], page=2)

    neaten.call(update, context)

    context.bot.send_photo.assert_not_called()
    context.bot.send_message.assert_called_once()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_message.call_args[1]['text'] == \
           "Could not locate the image by {} with image id {}.".format(username, image_id)
    assert context.bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_result_last_on_page(context):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        MockSubmission(post_id + 4, image_id=image_id + 16),
        MockSubmission(post_id + 3, image_id=image_id + 2),
        MockSubmission(post_id + 2, image_id=image_id + 1),
        submission
    ])

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.download_url
    assert context.bot.send_photo.call_args[1]['caption'] == submission.link
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_result_first_on_page(context):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        MockSubmission(post_id + 3, image_id=image_id + 16),
        MockSubmission(post_id + 2, image_id=image_id + 8)
    ], page=1)
    neaten.api.with_user_folder(username, "gallery", [
        submission,
        MockSubmission(post_id - 2, image_id=image_id - 2),
        MockSubmission(post_id - 7, image_id=image_id - 4),
        MockSubmission(post_id - 9, image_id=image_id - 10)
    ], page=2)

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.download_url
    assert context.bot.send_photo.call_args[1]['caption'] == submission.link
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_not_on_first_page_empty_second_page(context):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        MockSubmission(post_id + 3, image_id=image_id + 16),
        MockSubmission(post_id + 2, image_id=image_id + 8)
    ], page=1)
    neaten.api.with_user_folder(username, "gallery", [
    ], page=2)

    neaten.call(update, context)

    context.bot.send_photo.assert_not_called()
    context.bot.send_message.assert_called_once()
    assert context.bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_message.call_args[1]['text'] == \
           "Could not locate the image by {} with image id {}.".format(username, image_id)
    assert context.bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_result_in_scraps(context):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    update = MockTelegramUpdate.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    for page in [1, 2]:
        neaten.api.with_user_folder(username, "gallery", [
            MockSubmission(post_id + 1 + (3 - page) * 5, image_id=image_id + 16 + (3 - page) * 56),
            MockSubmission(post_id + (3 - page) * 5, image_id=image_id + (3 - page) * 56),
            MockSubmission(post_id - 2 + (3 - page) * 5, image_id=image_id - 27 + (3 - page) * 56),
            MockSubmission(post_id - 3 + (3 - page) * 5, image_id=image_id - 34 + (3 - page) * 56)
        ], page=page)
    neaten.api.with_user_folder(username, "gallery", [], page=3)
    neaten.api.with_user_folder(username, "scraps", [
        MockSubmission(post_id + 1, image_id=image_id + 16),
        submission,
        MockSubmission(post_id - 2, image_id=image_id - 27),
        MockSubmission(post_id - 3, image_id=image_id - 34)
    ], page=1)

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.download_url
    assert context.bot.send_photo.call_args[1]['caption'] == submission.link
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id
