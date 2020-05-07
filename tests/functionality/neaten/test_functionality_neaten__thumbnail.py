from unittest.mock import call

from functionalities.neaten import NeatenFunctionality
from tests.util.mock_export_api import MockExportAPI, MockSubmission
from tests.util.mock_telegram_update import MockTelegramUpdate


def test_thumbnail_link(context):
    post_id = 382632
    update = MockTelegramUpdate.with_message(
        text=f"https://t.facdn.net/{post_id}@400-1562445328.jpg"
    )
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.download_url
    assert context.bot.send_photo.call_args[1]['caption'] == submission.link
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_thumbnail_link_not_round(context):
    post_id = 382632
    update = MockTelegramUpdate.with_message(
        text=f"https://t.facdn.net/{post_id}@75-1562445328.jpg"
    )
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.download_url
    assert context.bot.send_photo.call_args[1]['caption'] == submission.link
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_thumbnail_link_big(context):
    post_id = 382632
    update = MockTelegramUpdate.with_message(
        text=f"https://t.facdn.net/{post_id}@1600-1562445328.jpg"
    )
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.download_url
    assert context.bot.send_photo.call_args[1]['caption'] == submission.link
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_doesnt_fire_on_avatar(context):
    update = MockTelegramUpdate.with_message(
        text="https://a.facdn.net/1538326752/geordie79.gif"
    )
    neaten = NeatenFunctionality(MockExportAPI())

    neaten.call(update, context)

    context.bot.send_photo.assert_not_called()
    context.bot.send_document.assert_not_called()
    context.bot.send_message.assert_not_called()
    context.bot.send_audio.assert_not_called()


def test_thumb_and_submission_link(context):
    post_id = 382632
    update = MockTelegramUpdate.with_message(
        text=f"https://t.facdn.net/{post_id}@1600-1562445328.jpg\nhttps://furaffinity.net/view/{post_id}"
    )
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.download_url
    assert context.bot.send_photo.call_args[1]['caption'] == submission.link
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_thumb_and_different_submission_link(context):
    post_id1 = 382632
    post_id2 = 382672
    update = MockTelegramUpdate.with_message(
        text=f"https://t.facdn.net/{post_id1}@1600-1562445328.jpg\nhttps://furaffinity.net/view/{post_id2}"
    )
    submission1 = MockSubmission(post_id1)
    submission2 = MockSubmission(post_id2)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submissions([submission1, submission2])

    neaten.call(update, context)

    context.bot.send_photo.assert_called()
    calls = [call(
        chat_id=update.message.chat_id,
        photo=submission.download_url,
        caption=submission.link,
        reply_to_message_id=update.message.message_id
    ) for submission in [submission1, submission2]]
    context.bot.send_photo.assert_has_calls(calls)
