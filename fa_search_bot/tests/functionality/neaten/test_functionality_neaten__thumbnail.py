from fa_search_bot.functionalities.neaten import NeatenFunctionality
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_telegram_update import MockTelegramUpdate


def test_thumbnail_link(context):
    post_id = 382632
    update = MockTelegramUpdate.with_message(
        text=f"https://t.furaffinity.net/{post_id}@400-1562445328.jpg"
    )
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_thumbnail_link__old_cdn(context):
    post_id = 382632
    update = MockTelegramUpdate.with_message(
        text=f"https://t.facdn.net/{post_id}@400-1562445328.jpg"
    )
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_thumbnail_link__newer_cdn(context):
    post_id = 382632
    update = MockTelegramUpdate.with_message(
        text=f"https://t2.facdn.net/{post_id}@400-1562445328.jpg"
    )
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_thumbnail_link_not_round(context):
    post_id = 382632
    update = MockTelegramUpdate.with_message(
        text=f"https://t.furaffinity.net/{post_id}@75-1562445328.jpg"
    )
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_thumbnail_link_big(context):
    post_id = 382632
    update = MockTelegramUpdate.with_message(
        text=f"https://t.furaffinity.net/{post_id}@1600-1562445328.jpg"
    )
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_doesnt_fire_on_avatar(context):
    update = MockTelegramUpdate.with_message(
        text="https://a.furaffinity.net/1538326752/geordie79.gif"
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
        text=f"https://t.furaffinity.net/{post_id}@1600-1562445328.jpg\nhttps://furaffinity.net/view/{post_id}"
    )
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_thumb_and_different_submission_link(context):
    post_id1 = 382632
    post_id2 = 382672
    update = MockTelegramUpdate.with_message(
        text=f"https://t.furaffinity.net/{post_id1}@1600-1562445328.jpg\nhttps://furaffinity.net/view/{post_id2}"
    )
    submission1 = MockSubmission(post_id1)
    submission2 = MockSubmission(post_id2)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submissions([submission1, submission2])

    neaten.call(update, context)

    submission1.send_message.assert_called_once()
    args1, _ = submission1.send_message.call_args
    assert args1[0] == context.bot
    assert args1[1] == update.message.chat_id
    assert args1[2] == update.message.message_id
    submission2.send_message.assert_called_once()
    args2, _ = submission2.send_message.call_args
    assert args2[0] == context.bot
    assert args2[1] == update.message.chat_id
    assert args2[2] == update.message.message_id
