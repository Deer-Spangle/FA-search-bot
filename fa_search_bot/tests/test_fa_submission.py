import unittest
from unittest import mock
from unittest.mock import patch

import requests_mock
import telegram

from fa_search_bot import bot as mqbot
from fa_search_bot.fa_submission import FASubmission, FASubmissionShort, FASubmissionFull, CantSendFileType, FAUser, \
    FAUserShort, \
    Rating
from fa_search_bot.functionalities.neaten import NeatenFunctionality
from fa_search_bot.tests.util.mock_method import MockMethod, MockMultiMethod
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder


# noinspection PyMethodMayBeStatic
class FAUserTest(unittest.TestCase):

    def test_constructor(self):
        name = "John"
        profile_name = "john"

        author = FAUser(name, profile_name)

        assert author.name == name
        assert author.profile_name == profile_name
        assert f"/user/{profile_name}" in author.link

    def test_from_short_dict(self):
        name = "John"
        profile_name = "john"

        author = FAUser.from_short_dict(
            {
                "name": name,
                "profile_name": profile_name
            }
        )

        assert author.name == name
        assert author.profile_name == profile_name
        assert f"/user/{profile_name}" in author.link

    def test_from_submission_dict(self):
        name = "John"
        profile_name = "john"

        author = FAUser.from_submission_dict(
            {
                "name": name,
                "profile_name": profile_name
            }
        )

        assert author.name == name
        assert author.profile_name == profile_name
        assert f"/user/{profile_name}" in author.link


# noinspection PyMethodMayBeStatic
class FAUserShortTest(unittest.TestCase):

    def test_constructor(self):
        name = "John"
        profile_name = "john"

        author = FAUserShort(name, profile_name)

        assert author.name == name
        assert author.profile_name == profile_name
        assert f"/user/{profile_name}" in author.link


# noinspection PyMethodMayBeStatic
class FASubmissionTest(unittest.TestCase):

    def test_constructor(self):
        post_id = "1242"

        submission = FASubmission(post_id)

        assert submission.submission_id == post_id
        assert NeatenFunctionality.FA_SUB_LINK.search(submission.link) is not None
        assert f"view/{post_id}" in submission.link

    def test_create_from_short_dict(self):
        builder = SubmissionBuilder()

        submission = FASubmission.from_short_dict(
            builder.build_search_json()
        )

        assert isinstance(submission, FASubmissionShort)
        assert submission.submission_id == builder.submission_id
        assert submission.link == builder.link

        assert submission.thumbnail_url == builder.thumbnail_url
        assert submission.title == builder.title
        assert submission.author.profile_name == builder.author.profile_name
        assert submission.author.name == builder.author.name
        assert submission.author.link == builder.author.link

    def test_create_from_full_dict(self):
        builder = SubmissionBuilder()

        submission = FASubmission.from_full_dict(
            builder.build_submission_json()
        )

        assert isinstance(submission, FASubmissionFull)
        assert submission.submission_id == builder.submission_id
        assert submission.link == builder.link

        assert submission.thumbnail_url == builder.thumbnail_url
        assert submission.title == builder.title
        assert submission.author.profile_name == builder.author.profile_name
        assert submission.author.name == builder.author.name
        assert submission.author.link == builder.author.link

        assert submission.download_url == builder.download_url
        assert submission.full_image_url == builder.full_image_url
        assert submission.description == builder.description
        assert submission.keywords == builder.keywords

    def test_create_short_dict_makes_thumb_bigger_75(self):
        builder = SubmissionBuilder(thumb_size=75)
        big_thumb_link = builder.thumbnail_url.replace("@75-", "@1600-")

        submission = FASubmission.from_short_dict(
            builder.build_search_json()
        )

        assert submission.thumbnail_url == big_thumb_link

    def test_make_thumbnail_bigger(self):
        post_id = "1234"
        image_id = "5324543"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        big_thumb_link = f"https://t.facdn.net/{post_id}@1600-{image_id}.jpg"

        big_link = FASubmission.make_thumbnail_bigger(thumb_link)

        assert big_link == big_thumb_link

    def test_make_thumbnail_bigger_size_75(self):
        post_id = "1234"
        image_id = "5324543"
        # Only available size not ending 0
        thumb_link = f"https://t.facdn.net/{post_id}@75-{image_id}.jpg"
        big_thumb_link = f"https://t.facdn.net/{post_id}@1600-{image_id}.jpg"

        big_link = FASubmission.make_thumbnail_bigger(thumb_link)

        assert big_link == big_thumb_link

    def test_id_from_link(self):
        post_id = "12874"
        link = f"https://furaffinity.net/view/{post_id}/"

        new_id = FASubmission.id_from_link(link)

        assert new_id == post_id

    @requests_mock.mock()
    def test_get_file_size(self, r):
        url = "http://example.com/file.jpg"
        size = 7567
        r.head(
            url,
            headers={
                "content-length": str(size)
            }
        )

        file_size = FASubmission._get_file_size(url)

        assert isinstance(size, int)
        assert file_size == size


# noinspection DuplicatedCode,PyMethodMayBeStatic
class FASubmissionShortTest(unittest.TestCase):

    def test_constructor(self):
        post_id = "1234"
        image_id = "5324543"
        link = f"https://furaffinity.net/view/{post_id}/"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        title = "Example post"
        author = FAUser.from_short_dict({"name": "John", "profile_name": "john"})

        submission = FASubmissionShort(post_id, thumb_link, title, author)

        assert isinstance(submission, FASubmissionShort)
        assert submission.submission_id == post_id
        assert submission.link == link
        assert submission.thumbnail_url == thumb_link
        assert submission.title == title
        assert submission.author == author

    def test_to_inline_query_result(self):
        post_id = "1234"
        image_id = "5324543"
        link = f"https://furaffinity.net/view/{post_id}/"
        thumb_url = f"https://t.facdn.net/{post_id}@1600-{image_id}.jpg"
        title = "Example post"
        author = FAUser.from_short_dict({"name": "John", "profile_name": "john"})
        submission = FASubmissionShort(post_id, thumb_url, title, author)

        query_result = submission.to_inline_query_result()

        assert query_result.id == post_id
        assert query_result.photo_url == thumb_url
        assert query_result.thumb_url == FASubmission.make_thumbnail_smaller(thumb_url)
        assert query_result.caption == link


# noinspection DuplicatedCode,PyMethodMayBeStatic
class FASubmissionFullTest(unittest.TestCase):

    def test_constructor(self):
        post_id = "1234"
        image_id = "5324543"
        link = f"https://furaffinity.net/view/{post_id}/"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        full_link = f"https://d.facdn.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.jpg"
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

        submission.send_message(bot, chat_id, message_id)

        bot.send_photo.assert_called_once()
        bot.send_document.assert_not_called()
        bot.send_message.assert_not_called()
        assert bot.send_photo.call_args[1]['chat_id'] == chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.full_image_url
        assert bot.send_photo.call_args[1]['caption'] == \
            f"{submission.link}\n<a href=\"{submission.download_url}\">Direct download</a>"
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.HTML

    @patch.object(mqbot, "MQBot")
    def test_send_message__with_prefix(self, bot):
        submission = SubmissionBuilder(file_ext="jpg", file_size=FASubmission.SIZE_LIMIT_IMAGE - 1) \
            .build_full_submission()
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(bot, chat_id, message_id, prefix="Update on a search")

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
