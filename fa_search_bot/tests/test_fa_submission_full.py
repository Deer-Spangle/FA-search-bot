import unittest
from unittest import mock
from unittest.mock import patch, Mock

import requests_mock
import telegram
import telethon
from telethon.tl.types import TypeInputPeer

from fa_search_bot import bot as mqbot
from fa_search_bot.fa_submission import FAUser, Rating, FASubmissionFull, CantSendFileType, FASubmission
from fa_search_bot.tests.test_fa_submission import loop
from fa_search_bot.tests.util.mock_method import MockMethod, MockMultiMethod
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder


class FASubmissionFullTest(unittest.TestCase):

    def test_constructor(self):
        post_id = "1234"
        image_id = "5324543"
        link = f"https://furaffinity.net/view/{post_id}/"
        thumb_link = f"https://t.furaffinity.net/{post_id}@400-{image_id}.jpg"
        full_link = f"https://d.furaffinity.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.jpg"
        title = "Example post"
        author = FAUser.from_short_dict({"name": "John", "profile_name": "john"})
        description = "This is an example post for testing"
        keywords = ["example", "test"]
        rating = Rating.GENERAL

        submission = FASubmissionFull(
            post_id, thumb_link, full_link, full_link, title, author, description, keywords, rating
        )

        assert isinstance(submission, FASubmissionFull)
        assert submission.submission_id == post_id
        assert submission.link == link
        assert submission.thumbnail_url == thumb_link
        assert submission.full_image_url == full_link
        assert submission.download_url == full_link
        assert submission.title == title
        assert submission.author == author
        assert submission.description == description
        assert submission.keywords == keywords
        assert submission.rating == rating

    @requests_mock.mock()
    def test_download_file_size(self, r):
        submission = SubmissionBuilder().build_full_submission()
        size = 23124
        r.head(
            submission.full_image_url,
            headers={
                "content-length": str(size)
            }
        )

        file_size = submission.download_file_size

        assert isinstance(file_size, int)
        assert file_size == size

        r.head(
            submission.full_image_url,
            status_code=404
        )

        file_size2 = submission.download_file_size

        assert isinstance(file_size2, int)
        assert file_size2 == size

    @patch.object(mqbot, "MQBot")
    def test_gif_submission(self, bot):
        submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
        chat_id = -9327622
        message_id = 2873292
        convert = MockMethod("output.mp4")
        submission._convert_gif = convert.call
        mock_open = mock.mock_open(read_data=b"data")
        mock_rename = MockMethod()

        with mock.patch("fa_search_bot.fa_submission.open", mock_open):
            with mock.patch("os.rename", mock_rename.call):
                submission.send_message(bot, chat_id, message_id)

        assert convert.called
        bot.send_photo.assert_not_called()
        bot.send_document.assert_called_once()
        assert bot.send_document.call_args[1]['chat_id'] == chat_id
        assert mock_rename.called
        assert mock_rename.args[0] == "output.mp4"
        assert mock_rename.args[1] == f"{submission.GIF_CACHE_DIR}/{submission.submission_id}.mp4"
        assert mock_open.call_args[0][0] == f"{submission.GIF_CACHE_DIR}/{submission.submission_id}.mp4"
        assert mock_open.call_args[0][1] == "rb"
        assert bot.send_document.call_args[1]['document'] == mock_open.return_value
        assert bot.send_document.call_args[1]['caption'] == submission.link
        assert bot.send_document.call_args[1]['reply_to_message_id'] == message_id

    @patch.object(mqbot, "MQBot")
    def test_gif_submission_from_cache(self, bot):
        submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
        chat_id = -9327622
        message_id = 2873292
        convert = MockMethod("output.mp4")
        submission._convert_gif = convert.call
        mock_open = mock.mock_open(read_data=b"data")
        mock_exists = MockMethod(True)

        with mock.patch("fa_search_bot.fa_submission.open", mock_open):
            with mock.patch("os.path.exists", mock_exists.call):
                submission.send_message(bot, chat_id, message_id)

        assert not convert.called
        bot.send_photo.assert_not_called()
        bot.send_document.assert_called_once()
        assert bot.send_document.call_args[1]['chat_id'] == chat_id
        assert mock_exists.called
        assert mock_exists.args[0] == f"{submission.GIF_CACHE_DIR}/{submission.submission_id}.mp4"
        assert mock_open.call_args[0][0] == f"{submission.GIF_CACHE_DIR}/{submission.submission_id}.mp4"
        assert mock_open.call_args[0][1] == "rb"
        assert bot.send_document.call_args[1]['document'] == mock_open.return_value
        assert bot.send_document.call_args[1]['caption'] == submission.link
        assert bot.send_document.call_args[1]['reply_to_message_id'] == message_id

    def test_convert_gif(self):
        submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
        mock_run = MockMethod("Test docker")
        mock_filesize = MockMethod(submission.SIZE_LIMIT_GIF - 10)
        submission._run_docker = mock_run.call

        with mock.patch("os.path.getsize", mock_filesize.call):
            output_path = submission._convert_gif(submission.download_url)

        assert output_path is not None
        assert output_path.endswith(".mp4")
        assert mock_run.called
        assert mock_run.args[1].startswith(f"-i {submission.download_url}")
        assert mock_run.args[1].endswith(f" /{output_path}")

    def test_convert_gif_two_pass(self):
        submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
        mock_run = MockMultiMethod(["Test docker", "27.5", "ffmpeg1", "ffmpeg2"])
        mock_filesize = MockMethod(submission.SIZE_LIMIT_GIF + 10)
        submission._run_docker = mock_run.call

        with mock.patch("os.path.getsize", mock_filesize.call):
            output_path = submission._convert_gif(submission.download_url)

        assert output_path is not None
        assert output_path.endswith(".mp4")
        assert mock_run.calls == 4
        # Initial ffmpeg call
        assert mock_run.args[0][1].startswith(f"-i {submission.download_url}")
        # ffprobe call
        assert mock_run.args[1][1].startswith("-show_entries format=duration")
        assert mock_run.kwargs[1]["entrypoint"] == "ffprobe"
        # First ffmpeg two pass call
        assert mock_run.args[2][1].startswith(f"-i {submission.download_url}")
        assert mock_run.args[2][1].endswith("-pass 1 -f mp4 /dev/null -y")
        # Second ffmpeg two pass call
        assert mock_run.args[3][1].startswith(f"-i {submission.download_url}")
        assert mock_run.args[3][1].endswith(f"-pass 2 {output_path} -y")

    @patch.object(mqbot, "MQBot")
    def test_convert_gif_failure(self, bot):
        submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
        chat_id = -9327622
        message_id = 2873292
        submission._convert_gif = lambda *args: (_ for _ in ()).throw(Exception)

        submission.send_message(bot, chat_id, message_id)

        bot.send_photo.assert_not_called()
        bot.send_document.assert_called_once()
        assert bot.send_document.call_args[1]['chat_id'] == chat_id
        assert bot.send_document.call_args[1]['document'] == submission.download_url
        assert bot.send_document.call_args[1]['caption'] == submission.link
        assert bot.send_document.call_args[1]['reply_to_message_id'] == message_id

    @patch.object(mqbot, "MQBot")
    def test_pdf_submission(self, bot):
        submission = SubmissionBuilder(file_ext="pdf", file_size=47453).build_full_submission()
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(bot, chat_id, message_id)

        bot.send_photo.assert_not_called()
        bot.send_document.assert_called_once()
        assert bot.send_document.call_args[1]['chat_id'] == chat_id
        assert bot.send_document.call_args[1]['document'] == submission.download_url
        assert bot.send_document.call_args[1]['caption'] == submission.link
        assert bot.send_document.call_args[1]['reply_to_message_id'] == message_id

    @patch.object(mqbot, "MQBot")
    def test_mp3_submission(self, bot):
        submission = SubmissionBuilder(file_ext="mp3", file_size=47453).build_full_submission()
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(bot, chat_id, message_id)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_not_called()
        bot.send_document.assert_not_called()
        bot.send_audio.assert_called_once()
        assert bot.send_audio.call_args[1]['chat_id'] == chat_id
        assert bot.send_audio.call_args[1]['audio'] == submission.download_url
        assert bot.send_audio.call_args[1]['caption'] == submission.link
        assert bot.send_audio.call_args[1]['reply_to_message_id'] == message_id

    @patch.object(mqbot, "MQBot")
    def test_txt_submission(self, bot):
        submission = SubmissionBuilder(file_ext="txt").build_full_submission()
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(bot, chat_id, message_id)

        bot.send_message.assert_not_called()
        bot.send_photo.assert_called_once()
        bot.send_document.assert_not_called()
        bot.send_audio.assert_not_called()
        assert bot.send_photo.call_args[1]['chat_id'] == chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.full_image_url
        assert bot.send_photo.call_args[1]['caption'] == \
            f"{submission.link}\n<a href=\"{submission.download_url}\">Direct download</a>"
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.HTML

    @patch.object(mqbot, "MQBot")
    def test_swf_submission(self, bot):
        submission = SubmissionBuilder(file_ext="swf", file_size=47453).build_full_submission()
        chat_id = -9327622
        message_id = 2873292

        try:
            submission.send_message(bot, chat_id, message_id)
            assert False, "Should have thrown exception."
        except CantSendFileType as e:
            assert str(e) == "I'm sorry, I can't neaten \".swf\" files."

    @patch.object(mqbot, "MQBot")
    def test_unknown_type_submission(self, bot):
        submission = SubmissionBuilder(file_ext="zzz", file_size=47453).build_full_submission()
        chat_id = -9327622
        message_id = 2873292

        try:
            submission.send_message(bot, chat_id, message_id)
            assert False, "Should have thrown exception."
        except CantSendFileType as e:
            assert str(e) == "I'm sorry, I don't understand that file extension (zzz)."

    @patch.object(mqbot, "MQBot")
    def test_image_just_under_size_limit(self, bot):
        submission = SubmissionBuilder(file_ext="jpg", file_size=FASubmission.SIZE_LIMIT_IMAGE - 1) \
            .build_full_submission()
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(bot, chat_id, message_id)

        bot.send_photo_with_backup.assert_called_once()
        assert bot.send_photo_with_backup.call_args[0][0] == chat_id
        assert bot.send_photo_with_backup.call_args[0][1]['photo'] == submission.download_url
        assert bot.send_photo_with_backup.call_args[0][2]['photo'] == submission.thumbnail_url
        assert bot.send_photo_with_backup.call_args[0][1]['caption'] == submission.link
        assert bot.send_photo_with_backup.call_args[0][2]['caption'] == \
            f"{submission.link}\n<a href=\"{submission.download_url}\">Direct download</a>"
        assert bot.send_photo_with_backup.call_args[0][1]['reply_to_message_id'] == message_id
        assert bot.send_photo_with_backup.call_args[0][2]['reply_to_message_id'] == message_id

    @patch.object(mqbot, "MQBot")
    def test_image_just_over_size_limit(self, bot):
        submission = SubmissionBuilder(file_ext="jpg", file_size=FASubmission.SIZE_LIMIT_IMAGE + 1) \
            .build_full_submission()
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(bot, chat_id, message_id)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.thumbnail_url
        assert bot.send_photo.call_args[1]['caption'] == \
            f"{submission.link}\n<a href=\"{submission.download_url}\">Direct download</a>"
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.HTML

    @patch.object(mqbot, "MQBot")
    def test_image_over_document_size_limit(self, bot):
        submission = SubmissionBuilder(file_ext="jpg", file_size=FASubmission.SIZE_LIMIT_DOCUMENT + 1) \
            .build_full_submission()
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(bot, chat_id, message_id)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.thumbnail_url
        assert bot.send_photo.call_args[1]['caption'] == \
            f"{submission.link}\n<a href=\"{submission.download_url}\">Direct download</a>"
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.HTML

    @patch.object(mqbot, "MQBot")
    def test_auto_doc_just_under_size_limit(self, bot):
        submission = SubmissionBuilder(file_ext="pdf", file_size=FASubmission.SIZE_LIMIT_DOCUMENT - 1) \
            .build_full_submission()
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(bot, chat_id, message_id)

        bot.send_document.assert_called_once()
        bot.send_photo.assert_not_called()
        bot.send_message.assert_not_called()
        assert bot.send_document.call_args[1]['chat_id'] == chat_id
        assert bot.send_document.call_args[1]['document'] == submission.download_url
        assert bot.send_document.call_args[1]['caption'] == submission.link
        assert bot.send_document.call_args[1]['reply_to_message_id'] == message_id

    @patch.object(mqbot, "MQBot")
    def test_auto_doc_just_over_size_limit(self, bot):
        submission = SubmissionBuilder(file_ext="pdf", file_size=FASubmission.SIZE_LIMIT_DOCUMENT + 1) \
            .build_full_submission()
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(client, chat, message_id)

        bot.send_photo.assert_called_once()
        bot.send_document.assert_not_called()
        bot.send_message.assert_not_called()
        assert bot.send_photo.call_args[1]['chat_id'] == chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.full_image_url
        assert bot.send_photo.call_args[1]['caption'] == \
            f"{submission.link}\n<a href=\"{submission.download_url}\">Direct download</a>"
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.HTML

    @patch.object(telethon, "TelegramClient")
    def test_send_message__with_prefix(self, client):
        submission = SubmissionBuilder(file_ext="jpg", file_size=FASubmission.SIZE_LIMIT_IMAGE - 1) \
            .build_full_submission()
        chat_id = -9327622
        chat = Mock(TypeInputPeer)
        chat.id = chat_id
        message_id = 2873292

        loop.run_until_complete(submission.send_message(client, chat, reply_to=message_id, prefix="Update on a search"))

        client.send_message.assert_called_once()
        bot.send_photo_with_backup.assert_called_once()
        assert bot.send_photo_with_backup.call_args[0][0] == chat_id
        assert bot.send_photo_with_backup.call_args[0][1]['photo'] == submission.download_url
        assert bot.send_photo_with_backup.call_args[0][2]['photo'] == submission.thumbnail_url
        assert submission.link in bot.send_photo_with_backup.call_args[0][1]['caption']
        assert "Update on a search\n" in bot.send_photo_with_backup.call_args[0][1]['caption']
        assert submission.link in bot.send_photo_with_backup.call_args[0][2]['caption']
        assert "Update on a search\n" in bot.send_photo_with_backup.call_args[0][2]['caption']
        assert bot.send_photo_with_backup.call_args[0][1]['reply_to_message_id'] == message_id
        assert bot.send_photo_with_backup.call_args[0][2]['reply_to_message_id'] == message_id

    @patch.object(mqbot, "MQBot")
    def test_send_message__without_prefix(self, bot):
        submission = SubmissionBuilder(file_ext="jpg", file_size=FASubmission.SIZE_LIMIT_IMAGE - 1) \
            .build_full_submission()
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(bot, chat_id, message_id)

        bot.send_photo_with_backup.assert_called_once()
        assert bot.send_photo_with_backup.call_args[0][0] == chat_id
        assert bot.send_photo_with_backup.call_args[0][1]['photo'] == submission.download_url
        assert bot.send_photo_with_backup.call_args[0][2]['photo'] == submission.thumbnail_url
        assert bot.send_photo_with_backup.call_args[0][1]['caption'] == submission.link
        assert bot.send_photo_with_backup.call_args[0][2]['caption'] == \
            f"{submission.link}\n<a href=\"{submission.download_url}\">Direct download</a>"
        assert bot.send_photo_with_backup.call_args[0][1]['reply_to_message_id'] == message_id
        assert bot.send_photo_with_backup.call_args[0][2]['reply_to_message_id'] == message_id