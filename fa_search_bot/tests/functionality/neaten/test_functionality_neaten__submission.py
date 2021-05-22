from telegram import Chat

from fa_search_bot.fa_export_api import CloudflareError
from fa_search_bot.fa_submission import FASubmission
from fa_search_bot.functionalities.neaten import NeatenFunctionality
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent, MockButton


def test_ignore_message(context):
    update = MockTelegramEvent.with_message(text="hello world")
    neaten = NeatenFunctionality(MockExportAPI())

    neaten.call(update, context)

    context.bot.send_message.assert_not_called()
    context.bot.send_photo.assert_not_called()


def test_ignore_link(context):
    update = MockTelegramEvent.with_message(text="http://example.com")
    neaten = NeatenFunctionality(MockExportAPI())

    neaten.call(update, context)

    context.bot.send_message.assert_not_called()
    context.bot.send_photo.assert_not_called()


def test_ignore_profile_link(context):
    update = MockTelegramEvent.with_message(text="https://www.furaffinity.net/user/fender/")
    neaten = NeatenFunctionality(MockExportAPI())

    neaten.call(update, context)

    context.bot.send_message.assert_not_called()
    context.bot.send_photo.assert_not_called()


def test_ignore_journal_link(context):
    update = MockTelegramEvent.with_message(text="https://www.furaffinity.net/journal/9150534/")
    neaten = NeatenFunctionality(MockExportAPI())

    neaten.call(update, context)

    context.bot.send_message.assert_not_called()
    context.bot.send_photo.assert_not_called()


def test_ignore_channel_post(context):
    post_id = 23636984
    update = MockTelegramEvent.with_channel_post(text=f"https://www.furaffinity.net/view/{post_id}/")
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_not_called()


def test_submission_link(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_submission_link_in_caption(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message().with_photo(caption=f"https://www.furaffinity.net/view/{post_id}/")
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_submission_group_chat(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=Chat.GROUP
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


def test_submission_link_in_group_caption(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(
        chat_type=Chat.GROUP
    ).with_photo(caption=f"https://www.furaffinity.net/view/{post_id}/")
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_not_called()


def test_submission_link_no_http(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(text="furaffinity.net/view/{}".format(post_id))
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_two_submission_links(context):
    post_id1 = 23636984
    post_id2 = 23636996
    update = MockTelegramEvent.with_message(
        text="furaffinity.net/view/{}\nfuraffinity.net/view/{}".format(post_id1, post_id2)
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


def test_duplicate_submission_links(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(
        text="furaffinity.net/view/{0}\nfuraffinity.net/view/{0}".format(post_id)
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


def test_deleted_submission(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(text="furaffinity.net/view/{}".format(post_id))
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
    update = MockTelegramEvent.with_message(text="furaffinity.net/view/{}".format(post_id), chat_type=Chat.GROUP)
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
    update = MockTelegramEvent.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
    submission = MockSubmission(post_id, file_ext="gif")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_pdf_submission(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
    submission = MockSubmission(post_id, file_ext="pdf")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_mp3_submission(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
    submission = MockSubmission(post_id, file_ext="mp3")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_txt_submission(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
    submission = MockSubmission(post_id, file_ext="txt")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_swf_submission(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=Chat.PRIVATE
    )
    submission = MockSubmission(post_id, file_ext="swf")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_swf_submission_groupchat(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(
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
    update = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=Chat.PRIVATE
    )
    submission = MockSubmission(post_id, file_ext="zzz")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_unknown_type_submission_groupchat(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(
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
    update = MockTelegramEvent.with_message(
        text="Hello",
        text_markdown_urled="[Hello](https://www.furaffinity.net/view/{}/)".format(post_id)
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


def test_link_in_button(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(
        text="Hello"
    ).with_buttons(
        [
            [
                MockButton("View on E621", "https://e621.net/post/show/1699284"),
                MockButton("View on FA", f"https://www.furaffinity.net/view/{post_id}")
            ],
            [
                MockButton("Visit my website", "https://example.com")
            ]
        ]
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


def test_image_just_under_size_limit(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(
        text="Hello",
        text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
    )
    submission = MockSubmission(post_id, file_size=FASubmission.SIZE_LIMIT_IMAGE - 1)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_image_just_over_size_limit(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(
        text="Hello",
        text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
    )
    submission = MockSubmission(post_id, file_size=FASubmission.SIZE_LIMIT_IMAGE + 1)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_image_over_document_size_limit(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(
        text="Hello",
        text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
    )
    submission = MockSubmission(post_id, file_size=FASubmission.SIZE_LIMIT_DOCUMENT + 1)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_auto_doc_just_under_size_limit(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(
        text="Hello",
        text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
    )
    submission = MockSubmission(post_id, file_ext="pdf", file_size=FASubmission.SIZE_LIMIT_DOCUMENT - 1)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_auto_doc_just_over_size_limit(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(
        text="Hello",
        text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
    )
    submission = MockSubmission(post_id, file_ext="pdf", file_size=FASubmission.SIZE_LIMIT_DOCUMENT + 1)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    neaten.call(update, context)

    submission.send_message.assert_called_once()
    args, _ = submission.send_message.call_args
    assert args[0] == context.bot
    assert args[1] == update.message.chat_id
    assert args[2] == update.message.message_id


def test_cloudflare_error(context):
    post_id = 23636984
    update = MockTelegramEvent.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
    submission = MockSubmission(post_id)
    api = MockExportAPI()
    neaten = NeatenFunctionality(api)
    
    def raise_cloudflare(*args, **kwargs):
        raise CloudflareError()
    api.get_full_submission = raise_cloudflare

    neaten.call(update, context)

    submission.send_message.assert_not_called()
    context.bot.send_photo.assert_not_called()
    context.bot.send_message.assert_called_with(
        chat_id=update.message.chat_id,
        reply_to_message_id=update.message.message_id,
        text=f"Furaffinity is currently under cloudflare protection, so I cannot neaten links."
    )
