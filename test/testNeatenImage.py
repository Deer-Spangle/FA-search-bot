import unittest

from unittest.mock import patch, call

import telegram
from telegram import Chat

from bot import NeatenFunctionality
from fa_submission import FASubmission
from test.util.mock_export_api import MockExportAPI, MockSubmission
from test.util.testTelegramUpdateObjects import MockTelegramUpdate


class NeatenImageTest(unittest.TestCase):

    def setUp(self) -> None:
        self.neaten = NeatenFunctionality(MockExportAPI())

    @patch.object(telegram, "Bot")
    def test_ignore_message(self, bot):
        update = MockTelegramUpdate.with_message(text="hello world")

        self.neaten.call(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_ignore_link(self, bot):
        update = MockTelegramUpdate.with_message(text="http://example.com")

        self.neaten.call(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_ignore_profile_link(self, bot):
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/user/fender/")

        self.neaten.call(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_ignore_journal_link(self, bot):
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/journal/9150534/")

        self.neaten.call(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_submission_link(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
        submission = MockSubmission(post_id)
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.download_url
        assert bot.send_photo.call_args[1]['caption'] == submission.link
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_submission_group_chat(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="https://www.furaffinity.net/view/{}/".format(post_id),
            chat_type=Chat.GROUP
        )
        submission = MockSubmission(post_id)
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.download_url
        assert bot.send_photo.call_args[1]['caption'] == submission.link
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_submission_link_no_http(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="furaffinity.net/view/{}".format(post_id))
        submission = MockSubmission(post_id)
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.download_url
        assert bot.send_photo.call_args[1]['caption'] == submission.link
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_two_submission_links(self, bot):
        post_id1 = 23636984
        post_id2 = 23636996
        update = MockTelegramUpdate.with_message(
            text="furaffinity.net/view/{}\nfuraffinity.net/view/{}".format(post_id1, post_id2)
        )
        submission1 = MockSubmission(post_id1)
        submission2 = MockSubmission(post_id2)
        self.neaten.api.with_submissions([submission1, submission2])

        self.neaten.call(bot, update)

        bot.send_photo.assert_called()
        calls = [call(
            chat_id=update.message.chat_id,
            photo=submission.download_url,
            caption=submission.link,
            reply_to_message_id=update.message.message_id
        ) for submission in [submission1, submission2]]
        bot.send_photo.assert_has_calls(calls)

    @patch.object(telegram, "Bot")
    def test_duplicate_submission_links(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="furaffinity.net/view/{0}\nfuraffinity.net/view/{0}".format(post_id)
        )
        submission = MockSubmission(post_id)
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.download_url
        assert bot.send_photo.call_args[1]['caption'] == submission.link
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_deleted_submission(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="furaffinity.net/view/{}".format(post_id))

        self.neaten.call(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_message.assert_called_once()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert "This doesn't seem to be a valid FA submission" in bot.send_message.call_args[1]['text']
        assert str(post_id) in bot.send_message.call_args[1]['text']
        assert bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_deleted_submission_group_chat(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="furaffinity.net/view/{}".format(post_id), chat_type=Chat.GROUP)

        self.neaten.call(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_message.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_gif_submission(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
        submission = MockSubmission(post_id, file_ext="gif")
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_document.assert_called_once()
        assert bot.send_document.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_document.call_args[1]['document'] == submission.download_url
        assert bot.send_document.call_args[1]['caption'] == submission.link
        assert bot.send_document.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_pdf_submission(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
        submission = MockSubmission(post_id, file_ext="pdf")
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_document.assert_called_once()
        assert bot.send_document.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_document.call_args[1]['document'] == submission.download_url
        assert bot.send_document.call_args[1]['caption'] == submission.link
        assert bot.send_document.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_mp3_submission(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
        submission = MockSubmission(post_id, file_ext="mp3")
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()
        bot.send_document.assert_not_called()
        bot.send_audio.assert_called_once()
        assert bot.send_audio.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_audio.call_args[1]['audio'] == submission.download_url
        assert bot.send_audio.call_args[1]['caption'] == submission.link
        assert bot.send_audio.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_txt_submission(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
        submission = MockSubmission(post_id, file_ext="txt")
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_called_once()
        bot.send_document.assert_not_called()
        bot.send_audio.assert_not_called()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.full_image_url
        assert bot.send_photo.call_args[1]['caption'] == \
            f"{submission.link}\n[Direct download]({submission.download_url})"
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.MARKDOWN

    @patch.object(telegram, "Bot")
    def test_swf_submission(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="https://www.furaffinity.net/view/{}/".format(post_id),
            chat_type=Chat.PRIVATE
        )
        submission = MockSubmission(post_id, file_ext="swf")
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_message.assert_called_once()
        bot.send_photo.assert_not_called()
        bot.send_document.assert_not_called()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == "I'm sorry, I can't neaten \".swf\" files."
        assert bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_swf_submission_groupchat(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="https://www.furaffinity.net/view/{}/".format(post_id),
            chat_type=Chat.GROUP
        )
        submission = MockSubmission(post_id, file_ext="swf")
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()
        bot.send_document.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_unknown_type_submission(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="https://www.furaffinity.net/view/{}/".format(post_id),
            chat_type=Chat.PRIVATE
        )
        submission = MockSubmission(post_id, file_ext="zzz")
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_message.assert_called_once()
        bot.send_photo.assert_not_called()
        bot.send_document.assert_not_called()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == "I'm sorry, I don't understand that file extension (zzz)."
        assert bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_unknown_type_submission_groupchat(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="https://www.furaffinity.net/view/{}/".format(post_id),
            chat_type=Chat.GROUP
        )
        submission = MockSubmission(post_id, file_ext="zzz")
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()
        bot.send_document.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_link_in_markdown(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="Hello",
            text_markdown_urled="[Hello](https://www.furaffinity.net/view/{}/)".format(post_id)
        )
        submission = MockSubmission(post_id)
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.download_url
        assert bot.send_photo.call_args[1]['caption'] == submission.link
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_image_just_under_size_limit(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="Hello",
            text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
        )
        submission = MockSubmission(post_id, file_size=FASubmission.SIZE_LIMIT_IMAGE - 1)
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.download_url
        assert bot.send_photo.call_args[1]['caption'] == submission.link
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_image_just_over_size_limit(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="Hello",
            text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
        )
        submission = MockSubmission(post_id, file_size=FASubmission.SIZE_LIMIT_IMAGE + 1)
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.thumbnail_url
        assert bot.send_photo.call_args[1]['caption'] == \
            f"{submission.link}\n[Direct download]({submission.download_url})"
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.MARKDOWN

    @patch.object(telegram, "Bot")
    def test_image_over_document_size_limit(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="Hello",
            text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
        )
        submission = MockSubmission(post_id, file_size=FASubmission.SIZE_LIMIT_DOCUMENT + 1)
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.thumbnail_url
        assert bot.send_photo.call_args[1]['caption'] == \
            f"{submission.link}\n[Direct download]({submission.download_url})"
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.MARKDOWN

    @patch.object(telegram, "Bot")
    def test_auto_doc_just_under_size_limit(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="Hello",
            text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
        )
        submission = MockSubmission(post_id, file_ext="gif", file_size=FASubmission.SIZE_LIMIT_DOCUMENT - 1)
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_document.assert_called_once()
        bot.send_photo.assert_not_called()
        bot.send_message.assert_not_called()
        assert bot.send_document.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_document.call_args[1]['document'] == submission.download_url
        assert bot.send_document.call_args[1]['caption'] == submission.link
        assert bot.send_document.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_auto_doc_just_over_size_limit(self, bot):
        post_id = 23636984
        update = MockTelegramUpdate.with_message(
            text="Hello",
            text_markdown_urled="https://www.furaffinity.net/view/{}/".format(post_id)
        )
        submission = MockSubmission(post_id, file_ext="pdf", file_size=FASubmission.SIZE_LIMIT_DOCUMENT + 1)
        self.neaten.api.with_submission(submission)

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        bot.send_document.assert_not_called()
        bot.send_message.assert_not_called()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.full_image_url
        assert bot.send_photo.call_args[1]['caption'] == \
            f"{submission.link}\n[Direct download]({submission.download_url})"
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.MARKDOWN
