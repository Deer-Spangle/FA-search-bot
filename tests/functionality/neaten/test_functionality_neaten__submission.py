from unittest import mock
from unittest.mock import call

import telegram
from telegram import Chat

from fa_submission import FASubmission
from functionalities.neaten import NeatenFunctionality
from tests.util.mock_export_api import MockExportAPI, MockSubmission
from tests.util.mock_method import MockMethod
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


def test_submission_link(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.download_url
    assert context.bot.send_photo.call_args[1]['caption'] == submission.link
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_submission_group_chat(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=Chat.GROUP
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


def test_submission_link_no_http(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(text="furaffinity.net/view/{}".format(post_id))
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.download_url
    assert context.bot.send_photo.call_args[1]['caption'] == submission.link
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_two_submission_links(context):
    post_id1 = 23636984
    post_id2 = 23636996
    update = MockTelegramUpdate.with_message(
        text="furaffinity.net/view/{}\nfuraffinity.net/view/{}".format(post_id1, post_id2)
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


def test_duplicate_submission_links(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(
        text="furaffinity.net/view/{0}\nfuraffinity.net/view/{0}".format(post_id)
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


def test_deleted_submission(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(text="furaffinity.net/view/{}".format(post_id))
    neaten = NeatenFunctionality(MockExportAPI())

    neaten.call(update, context)

    context.bot.send_photo.assert_not_called()
    context.bot.send_message.assert_called_with(
        chat_id=update.message.chat_id,
        reply_to_message_id=update.message.message_id,
        text=f"This doesn't seem to be a valid FA submission: https://www.furaffinity.net/view/{post_id}/"
    )


def test_deleted_submission_group_chat(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(text="furaffinity.net/view/{}".format(post_id), chat_type=Chat.GROUP)
    neaten = NeatenFunctionality(MockExportAPI())

    neaten.call(update, context)

    context.bot.send_photo.assert_not_called()
    context.bot.send_message.assert_called_with(
        chat_id=update.message.chat_id,
        text="⏳ Neatening image link",
        reply_to_message_id=update.message.message_id
    )
    context.bot.delete_message.assert_called_with(
        update.message.chat_id,
        context._sent_message_ids[0]
    )


def test_gif_submission(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
    submission = MockSubmission(post_id, file_ext="gif")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)
    convert = MockMethod("output.gif")
    submission._convert_gif = convert.call
    mock_open = mock.mock_open(read_data=b"data")

    with mock.patch("fa_submission.open", mock_open):
        neaten.call(update, context)

    assert convert.called
    context.bot.send_photo.assert_not_called()
    context.bot.send_document.assert_called_once()
    assert context.bot.send_document.call_args[1]['chat_id'] == update.message.chat_id
    assert mock_open.call_args[0][0] == "output.gif"
    assert mock_open.call_args[0][1] == "rb"
    assert context.bot.send_document.call_args[1]['document'] == mock_open.return_value
    assert context.bot.send_document.call_args[1]['caption'] == submission.link
    assert context.bot.send_document.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_pdf_submission(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
    submission = MockSubmission(post_id, file_ext="pdf")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_photo.assert_not_called()
    context.bot.send_document.assert_called_once()
    assert context.bot.send_document.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_document.call_args[1]['document'] == submission.download_url
    assert context.bot.send_document.call_args[1]['caption'] == submission.link
    assert context.bot.send_document.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_mp3_submission(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
    submission = MockSubmission(post_id, file_ext="mp3")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_audio.assert_called_with(
        chat_id=update.message.chat_id,
        audio=submission.download_url,
        caption=submission.link,
        reply_to_message_id=update.message.message_id
    )


def test_txt_submission(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
    submission = MockSubmission(post_id, file_ext="txt")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_photo.assert_called_with(
        chat_id=update.message.chat_id,
        photo=submission.full_image_url,
        caption=f"{submission.link}\n[Direct download]({submission.download_url})",
        reply_to_message_id=update.message.message_id,
        parse_mode=telegram.ParseMode.MARKDOWN
    )


def test_swf_submission(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=Chat.PRIVATE
    )
    submission = MockSubmission(post_id, file_ext="swf")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_photo.assert_not_called()
    context.bot.send_document.assert_not_called()
    context.bot.send_message.assert_called_with(
        chat_id=update.message.chat_id,
        text="I'm sorry, I can't neaten \".swf\" files.",
        reply_to_message_id=update.message.message_id
    )


def test_swf_submission_groupchat(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=Chat.GROUP
    )
    submission = MockSubmission(post_id, file_ext="swf")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_photo.assert_not_called()
    context.bot.send_document.assert_not_called()
    context.bot.send_message.assert_called_with(
        chat_id=update.message.chat_id,
        text="⏳ Neatening image link",
        reply_to_message_id=update.message.message_id
    )
    context.bot.delete_message.assert_called_with(
        update.message.chat_id,
        context._sent_message_ids[0]
    )


def test_unknown_type_submission(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=Chat.PRIVATE
    )
    submission = MockSubmission(post_id, file_ext="zzz")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_photo.assert_not_called()
    context.bot.send_document.assert_not_called()
    context.bot.send_message.assert_called_with(
        chat_id=update.message.chat_id,
        text="I'm sorry, I don't understand that file extension (zzz).",
        reply_to_message_id=update.message.message_id
    )


def test_unknown_type_submission_groupchat(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=Chat.GROUP
    )
    submission = MockSubmission(post_id, file_ext="zzz")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_photo.assert_not_called()
    context.bot.send_document.assert_not_called()
    context.bot.send_message.assert_called_with(
        chat_id=update.message.chat_id,
        text="⏳ Neatening image link",
        reply_to_message_id=update.message.message_id
    )
    context.bot.delete_message.assert_called_with(
        update.message.chat_id,
        context._sent_message_ids[0]
    )


def test_link_in_markdown(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(
        text="Hello",
        text_markdown_urled="[Hello](https://www.furaffinity.net/view/{}/)".format(post_id)
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


def test_image_just_under_size_limit(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(
        text="Hello",
        text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
    )
    submission = MockSubmission(post_id, file_size=FASubmission.SIZE_LIMIT_IMAGE - 1)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.download_url
    assert context.bot.send_photo.call_args[1]['caption'] == submission.link
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id


def test_image_just_over_size_limit(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(
        text="Hello",
        text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
    )
    submission = MockSubmission(post_id, file_size=FASubmission.SIZE_LIMIT_IMAGE + 1)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.thumbnail_url
    assert context.bot.send_photo.call_args[1]['caption'] == \
           f"{submission.link}\n[Direct download]({submission.download_url})"
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id
    assert context.bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.MARKDOWN


def test_image_over_document_size_limit(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(
        text="Hello",
        text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
    )
    submission = MockSubmission(post_id, file_size=FASubmission.SIZE_LIMIT_DOCUMENT + 1)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_photo.assert_called_once()
    assert context.bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
    assert context.bot.send_photo.call_args[1]['photo'] == submission.thumbnail_url
    assert context.bot.send_photo.call_args[1]['caption'] == \
           f"{submission.link}\n[Direct download]({submission.download_url})"
    assert context.bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id
    assert context.bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.MARKDOWN


def test_auto_doc_just_under_size_limit(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(
        text="Hello",
        text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
    )
    submission = MockSubmission(post_id, file_ext="pdf", file_size=FASubmission.SIZE_LIMIT_DOCUMENT - 1)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_document.assert_called_with(
        chat_id=update.message.chat_id,
        document=submission.download_url,
        caption=submission.link,
        reply_to_message_id=update.message.message_id
    )


def test_auto_doc_just_over_size_limit(context):
    post_id = 23636984
    update = MockTelegramUpdate.with_message(
        text="Hello",
        text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
    )
    submission = MockSubmission(post_id, file_ext="pdf", file_size=FASubmission.SIZE_LIMIT_DOCUMENT + 1)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    context.bot.send_document.assert_not_called()
    context.bot.send_photo.assert_called_with(
        chat_id=update.message.chat_id,
        photo=submission.full_image_url,
        caption=f"{submission.link}\n[Direct download]({submission.download_url})",
        reply_to_message_id=update.message.message_id,
        parse_mode=telegram.ParseMode.MARKDOWN
    )
