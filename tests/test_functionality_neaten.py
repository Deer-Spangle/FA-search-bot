import unittest

from unittest.mock import patch, call

import telegram
from telegram import Chat

from functionalities.neaten import NeatenFunctionality
from fa_submission import FASubmission
from tests.util.mock_export_api import MockExportAPI, MockSubmission
from tests.util.mock_telegram_update import MockTelegramUpdate


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


class NeatenDirectImageTest(unittest.TestCase):

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
    def test_direct_link(self, bot):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        goal_submission = MockSubmission(post_id, image_id=image_id)
        self.neaten.api.with_user_folder(username, "gallery", [
            goal_submission,
            MockSubmission(post_id-1, image_id=image_id-15)
        ])

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == goal_submission.download_url
        assert bot.send_photo.call_args[1]['caption'] == goal_submission.link
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_direct_no_match(self, bot):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        for folder in ['gallery', 'scraps']:
            self.neaten.api.with_user_folder(username, folder, [
                MockSubmission(post_id, image_id=image_id+4),
                MockSubmission(post_id-1, image_id=image_id-15)
            ])

        self.neaten.call(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_message.assert_called_once()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == \
            "Could not locate the image by {} with image id {}.".format(username, image_id)
        assert bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_direct_no_match_groupchat(self, bot):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id),
            chat_type=Chat.GROUP
        )
        for folder in ['gallery', 'scraps']:
            self.neaten.api.with_user_folder(username, folder, [
                MockSubmission(post_id, image_id=image_id+4),
                MockSubmission(post_id-1, image_id=image_id-15)
            ])

        self.neaten.call(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_message.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_two_direct_links(self, bot):
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
        self.neaten.api.with_user_folder(username, "gallery", [
            submission1,
            submission2,
            MockSubmission(post_id2-1, image_id=image_id2-15)
        ])

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
    def test_duplicate_direct_link(self, bot):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png ".format(username, image_id)*2
        )
        submission = MockSubmission(post_id, image_id=image_id)
        self.neaten.api.with_user_folder(username, "gallery", [
            submission,
            MockSubmission(post_id-1, image_id=image_id-15)
        ])

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.download_url
        assert bot.send_photo.call_args[1]['caption'] == submission.link
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_direct_link_and_matching_submission_link(self, bot):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png https://furaffinity.net/view/{2}/".format(
                username, image_id, post_id
            )
        )
        submission = MockSubmission(post_id, image_id=image_id)
        self.neaten.api.with_user_folder(username, "gallery", [
            submission,
            MockSubmission(post_id-1, image_id=image_id-15)
        ])

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.download_url
        assert bot.send_photo.call_args[1]['caption'] == submission.link
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_direct_link_and_different_submission_link(self, bot):
        username = "fender"
        image_id1 = 1560331512
        image_id2 = image_id1+300
        post_id1 = 232347
        post_id2 = 233447
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png https://furaffinity.net/view/{2}/".format(
                username, image_id1, post_id2
            )
        )
        submission1 = MockSubmission(post_id1, image_id=image_id1)
        submission2 = MockSubmission(post_id2, image_id=image_id2)
        self.neaten.api.with_user_folder(username, "gallery", [
            submission2,
            submission1,
            MockSubmission(post_id1-1, image_id=image_id1-15)
        ])

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
    def test_submission_link_and_different_direct_link(self, bot):
        username = "fender"
        image_id1 = 1560331512
        image_id2 = image_id1+300
        post_id1 = 232347
        post_id2 = 233447
        update = MockTelegramUpdate.with_message(
            text="https://furaffinity.net/view/{2}/ http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(
                username, image_id1, post_id2
            )
        )
        submission1 = MockSubmission(post_id1, image_id=image_id1)
        submission2 = MockSubmission(post_id2, image_id=image_id2)
        self.neaten.api.with_user_folder(username, "gallery", [
            submission2,
            submission1,
            MockSubmission(post_id1-1, image_id=image_id1-15)
        ])

        self.neaten.call(bot, update)

        bot.send_photo.assert_called()
        calls = [call(
            chat_id=update.message.chat_id,
            photo=submission.download_url,
            caption=submission.link,
            reply_to_message_id=update.message.message_id
        ) for submission in [submission2, submission1]]
        bot.send_photo.assert_has_calls(calls)

    @patch.object(telegram, "Bot")
    def test_result_on_first_page(self, bot):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        submission = MockSubmission(post_id, image_id=image_id)
        self.neaten.api.with_user_folder(username, "gallery", [
            MockSubmission(post_id+1, image_id=image_id+16),
            submission,
            MockSubmission(post_id-2, image_id=image_id-27),
            MockSubmission(post_id-3, image_id=image_id-34)
        ])

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.download_url
        assert bot.send_photo.call_args[1]['caption'] == submission.link
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_result_on_third_page(self, bot):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        for page in [1, 2, 3]:
            self.neaten.api.with_user_folder(username, "gallery", [
                MockSubmission(post_id+1 + (3-page)*5, image_id=image_id+16 + (3-page)*56),
                MockSubmission(post_id + (3-page)*5, image_id=image_id + (3-page)*56),
                MockSubmission(post_id-2 + (3-page)*5, image_id=image_id-27 + (3-page)*56),
                MockSubmission(post_id-3 + (3-page)*5, image_id=image_id-34 + (3-page)*56)
            ], page=page)
        submission = self.neaten.api.get_full_submission(str(post_id))

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.download_url
        assert bot.send_photo.call_args[1]['caption'] == submission.link
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_result_missing_from_first_page(self, bot):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        self.neaten.api.with_user_folder(username, "gallery", [
            MockSubmission(post_id+1, image_id=image_id+16),
            MockSubmission(post_id, image_id=image_id+3),
            MockSubmission(post_id-2, image_id=image_id-27),
            MockSubmission(post_id-3, image_id=image_id-34)
        ])

        self.neaten.call(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_message.assert_called_once()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == \
            "Could not locate the image by {} with image id {}.".format(username, image_id)
        assert bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_result_missing_from_second_page(self, bot):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        for page in [1, 2]:
            self.neaten.api.with_user_folder(username, "gallery", [
                MockSubmission(post_id+1 + (2-page)*6, image_id=image_id+16 + (2-page)*56),
                MockSubmission(post_id+0 + (2-page)*6, image_id=image_id+3 + (2-page)*56),
                MockSubmission(post_id-2 + (2-page)*6, image_id=image_id-27 + (2-page)*56),
                MockSubmission(post_id-3 + (2-page)*6, image_id=image_id-34 + (2-page)*56)
            ], page=page)

        self.neaten.call(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_message.assert_called_once()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == \
            "Could not locate the image by {} with image id {}.".format(username, image_id)
        assert bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_result_missing_between_pages(self, bot):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        self.neaten.api.with_user_folder(username, "gallery", [
            MockSubmission(post_id+1, image_id=image_id+16),
            MockSubmission(post_id, image_id=image_id+3)
        ], page=1)
        self.neaten.api.with_user_folder(username, "gallery", [
            MockSubmission(post_id-2, image_id=image_id-27),
            MockSubmission(post_id-3, image_id=image_id-34)
        ], page=2)

        self.neaten.call(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_message.assert_called_once()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == \
            "Could not locate the image by {} with image id {}.".format(username, image_id)
        assert bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_result_last_on_page(self, bot):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        submission = MockSubmission(post_id, image_id=image_id)
        self.neaten.api.with_user_folder(username, "gallery", [
            MockSubmission(post_id+4, image_id=image_id+16),
            MockSubmission(post_id+3, image_id=image_id+2),
            MockSubmission(post_id+2, image_id=image_id+1),
            submission
        ])

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.download_url
        assert bot.send_photo.call_args[1]['caption'] == submission.link
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_result_first_on_page(self, bot):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        submission = MockSubmission(post_id, image_id=image_id)
        self.neaten.api.with_user_folder(username, "gallery", [
            MockSubmission(post_id+3, image_id=image_id+16),
            MockSubmission(post_id+2, image_id=image_id+8)
        ], page=1)
        self.neaten.api.with_user_folder(username, "gallery", [
            submission,
            MockSubmission(post_id-2, image_id=image_id-2),
            MockSubmission(post_id-7, image_id=image_id-4),
            MockSubmission(post_id-9, image_id=image_id-10)
        ], page=2)

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.download_url
        assert bot.send_photo.call_args[1]['caption'] == submission.link
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_not_on_first_page_empty_second_page(self, bot):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        self.neaten.api.with_user_folder(username, "gallery", [
            MockSubmission(post_id+3, image_id=image_id+16),
            MockSubmission(post_id+2, image_id=image_id+8)
        ], page=1)
        self.neaten.api.with_user_folder(username, "gallery", [
        ], page=2)

        self.neaten.call(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_message.assert_called_once()
        assert bot.send_message.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_message.call_args[1]['text'] == \
            "Could not locate the image by {} with image id {}.".format(username, image_id)
        assert bot.send_message.call_args[1]['reply_to_message_id'] == update.message.message_id

    @patch.object(telegram, "Bot")
    def test_result_in_scraps(self, bot):
        username = "fender"
        image_id = 1560331512
        post_id = 232347
        update = MockTelegramUpdate.with_message(
            text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
        )
        submission = MockSubmission(post_id, image_id=image_id)
        for page in [1, 2]:
            self.neaten.api.with_user_folder(username, "gallery", [
                MockSubmission(post_id+1 + (3-page)*5, image_id=image_id+16 + (3-page)*56),
                MockSubmission(post_id + (3-page)*5, image_id=image_id + (3-page)*56),
                MockSubmission(post_id-2 + (3-page)*5, image_id=image_id-27 + (3-page)*56),
                MockSubmission(post_id-3 + (3-page)*5, image_id=image_id-34 + (3-page)*56)
            ], page=page)
        self.neaten.api.with_user_folder(username, "gallery", [], page=3)
        self.neaten.api.with_user_folder(username, "scraps", [
            MockSubmission(post_id+1, image_id=image_id+16),
            submission,
            MockSubmission(post_id-2, image_id=image_id-27),
            MockSubmission(post_id-3, image_id=image_id-34)
        ], page=1)

        self.neaten.call(bot, update)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == update.message.chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.download_url
        assert bot.send_photo.call_args[1]['caption'] == submission.link
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == update.message.message_id


class NeatenImageThumbnailTest(unittest.TestCase):

    def setUp(self) -> None:
        self.neaten = NeatenFunctionality(MockExportAPI())

    @patch.object(telegram, "Bot")
    def test_thumbnail_link(self, bot):
        post_id = 382632
        update = MockTelegramUpdate.with_message(
            text=f"https://t.facdn.net/{post_id}@400-1562445328.jpg"
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
    def test_thumbnail_link_not_round(self, bot):
        post_id = 382632
        update = MockTelegramUpdate.with_message(
            text=f"https://t.facdn.net/{post_id}@75-1562445328.jpg"
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
    def test_thumbnail_link_big(self, bot):
        post_id = 382632
        update = MockTelegramUpdate.with_message(
            text=f"https://t.facdn.net/{post_id}@1600-1562445328.jpg"
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
    def test_doesnt_fire_on_avatar(self, bot):
        update = MockTelegramUpdate.with_message(
            text="https://a.facdn.net/1538326752/geordie79.gif"
        )

        self.neaten.call(bot, update)

        bot.send_photo.assert_not_called()
        bot.send_document.assert_not_called()
        bot.send_message.assert_not_called()
        bot.send_audio.assert_not_called()

    @patch.object(telegram, "Bot")
    def test_thumb_and_submission_link(self, bot):
        post_id = 382632
        update = MockTelegramUpdate.with_message(
            text=f"https://t.facdn.net/{post_id}@1600-1562445328.jpg\nhttps://furaffinity.net/view/{post_id}"
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
    def test_thumb_and_different_submission_link(self, bot):
        post_id1 = 382632
        post_id2 = 382672
        update = MockTelegramUpdate.with_message(
            text=f"https://t.facdn.net/{post_id1}@1600-1562445328.jpg\nhttps://furaffinity.net/view/{post_id2}"
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
