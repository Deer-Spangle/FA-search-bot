import unittest

from unittest.mock import patch
import requests_mock
import telegram

from bot import NeatenFunctionality
from fa_submission import FASubmission, FASubmissionShort, FASubmissionFull, CantSendFileType


class FASubmissionTest(unittest.TestCase):

    def test_constructor(self):
        post_id = "1242"

        submission = FASubmission(post_id)

        assert submission.submission_id == post_id
        assert NeatenFunctionality.FA_SUB_LINK.search(submission.link) is not None
        assert f"view/{post_id}" in submission.link

    def test_create_from_short_dict(self):
        post_id = "1234"
        image_id = "5324543"
        link = f"https://furaffinity.net/view/{post_id}/"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        big_thumb_link = f"https://t.facdn.net/{post_id}@1600-{image_id}.jpg"

        submission = FASubmission.from_short_dict(
            {
                "id": post_id,
                "link": link,
                "thumbnail": thumb_link
            }
        )

        assert isinstance(submission, FASubmissionShort)
        assert submission.submission_id == post_id
        assert submission.link == link
        assert submission.thumbnail_url == big_thumb_link

    def test_create_from_full_dict(self):
        post_id = "1234"
        image_id = "5324543"
        link = f"https://furaffinity.net/view/{post_id}/"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        big_thumb_link = f"https://t.facdn.net/{post_id}@1600-{image_id}.jpg"
        full_link = f"https://d.facdn.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.jpg"

        submission = FASubmission.from_full_dict(
            {
                "link": link,
                "thumbnail": thumb_link,
                "download": full_link,
                "full": full_link
            }
        )

        assert isinstance(submission, FASubmissionFull)
        assert submission.submission_id == post_id
        assert submission.link == link
        assert submission.thumbnail_url == big_thumb_link
        assert submission.full_image_url == full_link
        assert submission.download_url == full_link

    def test_create_short_dict_makes_thumb_bigger_75(self):
        post_id = "1234"
        image_id = "5324543"
        link = f"https://furaffinity.net/view/{post_id}/"
        thumb_link = f"https://t.facdn.net/{post_id}@75-{image_id}.jpg"
        big_thumb_link = f"https://t.facdn.net/{post_id}@1600-{image_id}.jpg"

        submission = FASubmission.from_short_dict(
            {
                "id": post_id,
                "link": link,
                "thumbnail": thumb_link
            }
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


class FASubmissionShortTest(unittest.TestCase):

    def test_constructor(self):
        post_id = "1234"
        image_id = "5324543"
        link = f"https://furaffinity.net/view/{post_id}/"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"

        submission = FASubmissionShort(post_id, thumb_link)

        assert isinstance(submission, FASubmissionShort)
        assert submission.submission_id == post_id
        assert submission.link == link
        assert submission.thumbnail_url == thumb_link

    def test_to_inline_query_result(self):
        post_id = "1234"
        image_id = "5324543"
        link = f"https://furaffinity.net/view/{post_id}/"
        thumb_url = f"https://t.facdn.net/{post_id}@1600-{image_id}.jpg"
        submission = FASubmissionShort(post_id, thumb_url)

        query_result = submission.to_inline_query_result()

        assert query_result.id == post_id
        assert query_result.photo_url == thumb_url
        assert query_result.thumb_url == FASubmission.make_thumbnail_smaller(thumb_url)
        assert query_result.caption == link


class FASubmissionFullTest(unittest.TestCase):

    def test_constructor(self):
        post_id = "1234"
        image_id = "5324543"
        link = f"https://furaffinity.net/view/{post_id}/"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        full_link = f"https://d.facdn.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.jpg"

        submission = FASubmissionFull(post_id, thumb_link, full_link, full_link)

        assert isinstance(submission, FASubmissionFull)
        assert submission.submission_id == post_id
        assert submission.link == link
        assert submission.thumbnail_url == thumb_link
        assert submission.full_image_url == full_link
        assert submission.download_url == full_link

    @requests_mock.mock()
    def test_download_file_size(self, r):
        post_id = "1234"
        image_id = "5324543"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        full_link = f"https://d.facdn.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.jpg"
        submission = FASubmissionFull(post_id, thumb_link, full_link, full_link)
        size = 23124
        r.head(
            full_link,
            headers={
                "content-length": str(size)
            }
        )

        file_size = submission.download_file_size

        assert isinstance(file_size, int)
        assert file_size == size

        r.head(
            full_link,
            status_code=404
        )

        file_size2 = submission.download_file_size

        assert isinstance(file_size2, int)
        assert file_size2 == size

    @patch.object(telegram, "Bot")
    def test_gif_submission(self, bot):
        post_id = "1234"
        image_id = "5324543"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        download_link = f"https://d.facdn.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.gif"
        submission = FASubmissionFull(post_id, thumb_link, download_link, download_link)
        submission._download_file_size = 47453
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(bot, chat_id, message_id)

        bot.send_photo.assert_not_called()
        bot.send_document.assert_called_once()
        assert bot.send_document.call_args[1]['chat_id'] == chat_id
        assert bot.send_document.call_args[1]['document'] == submission.download_url
        assert bot.send_document.call_args[1]['caption'] == submission.link
        assert bot.send_document.call_args[1]['reply_to_message_id'] == message_id

    @patch.object(telegram, "Bot")
    def test_pdf_submission(self, bot):
        post_id = "1234"
        image_id = "5324543"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        download_link = f"https://d.facdn.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.pdf"
        full_link = f"{download_link}.jpg"
        submission = FASubmissionFull(post_id, thumb_link, download_link, full_link)
        submission._download_file_size = 47453
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(bot, chat_id, message_id)

        bot.send_photo.assert_not_called()
        bot.send_document.assert_called_once()
        assert bot.send_document.call_args[1]['chat_id'] == chat_id
        assert bot.send_document.call_args[1]['document'] == submission.download_url
        assert bot.send_document.call_args[1]['caption'] == submission.link
        assert bot.send_document.call_args[1]['reply_to_message_id'] == message_id

    @patch.object(telegram, "Bot")
    def test_mp3_submission(self, bot):
        post_id = "1234"
        image_id = "5324543"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        download_link = f"https://d.facdn.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.mp3"
        full_link = f"{download_link}.jpg"
        submission = FASubmissionFull(post_id, thumb_link, download_link, full_link)
        submission._download_file_size = 47453
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

    @patch.object(telegram, "Bot")
    def test_txt_submission(self, bot):
        post_id = "1234"
        image_id = "5324543"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        download_link = f"https://d.facdn.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.txt"
        full_link = f"{download_link}.jpg"
        submission = FASubmissionFull(post_id, thumb_link, download_link, full_link)
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
            f"{submission.link}\n[Direct download]({submission.download_url})"
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.MARKDOWN

    @patch.object(telegram, "Bot")
    def test_swf_submission(self, bot):
        post_id = "1234"
        image_id = "5324543"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        download_link = f"https://d.facdn.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.swf"
        full_link = f"{download_link}.jpg"
        submission = FASubmissionFull(post_id, thumb_link, download_link, full_link)
        submission._download_file_size = 47453
        chat_id = -9327622
        message_id = 2873292

        try:
            submission.send_message(bot, chat_id, message_id)
            assert False, "Should have thrown exception."
        except CantSendFileType as e:
            assert str(e) == "I'm sorry, I can't neaten \".swf\" files."

    @patch.object(telegram, "Bot")
    def test_unknown_type_submission(self, bot):
        post_id = "1234"
        image_id = "5324543"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        download_link = f"https://d.facdn.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.zzz"
        full_link = f"{download_link}.jpg"
        submission = FASubmissionFull(post_id, thumb_link, download_link, full_link)
        submission._download_file_size = 47453
        chat_id = -9327622
        message_id = 2873292

        try:
            submission.send_message(bot, chat_id, message_id)
            assert False, "Should have thrown exception."
        except CantSendFileType as e:
            assert str(e) == "I'm sorry, I don't understand that file extension (zzz)."

    @patch.object(telegram, "Bot")
    def test_image_just_under_size_limit(self, bot):
        post_id = "1234"
        image_id = "5324543"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        download_link = f"https://d.facdn.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.jpg"
        full_link = download_link
        submission = FASubmissionFull(post_id, thumb_link, download_link, full_link)
        submission._download_file_size = FASubmission.SIZE_LIMIT_IMAGE - 1
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(bot, chat_id, message_id)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.download_url
        assert bot.send_photo.call_args[1]['caption'] == submission.link
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == message_id

    @patch.object(telegram, "Bot")
    def test_image_just_over_size_limit(self, bot):
        post_id = "1234"
        image_id = "5324543"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        download_link = f"https://d.facdn.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.jpg"
        full_link = download_link
        submission = FASubmissionFull(post_id, thumb_link, download_link, full_link)
        submission._download_file_size = FASubmission.SIZE_LIMIT_IMAGE + 1
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(bot, chat_id, message_id)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.thumbnail_url
        assert bot.send_photo.call_args[1]['caption'] == \
            f"{submission.link}\n[Direct download]({submission.download_url})"
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.MARKDOWN

    @patch.object(telegram, "Bot")
    def test_image_over_document_size_limit(self, bot):
        post_id = "1234"
        image_id = "5324543"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        download_link = f"https://d.facdn.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.jpg"
        full_link = download_link
        submission = FASubmissionFull(post_id, thumb_link, download_link, full_link)
        submission._download_file_size = FASubmission.SIZE_LIMIT_DOCUMENT + 1
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(bot, chat_id, message_id)

        bot.send_photo.assert_called_once()
        assert bot.send_photo.call_args[1]['chat_id'] == chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.thumbnail_url
        assert bot.send_photo.call_args[1]['caption'] == \
            f"{submission.link}\n[Direct download]({submission.download_url})"
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.MARKDOWN

    @patch.object(telegram, "Bot")
    def test_auto_doc_just_under_size_limit(self, bot):
        post_id = "1234"
        image_id = "5324543"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        download_link = f"https://d.facdn.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.gif"
        full_link = download_link
        submission = FASubmissionFull(post_id, thumb_link, download_link, full_link)
        submission._download_file_size = FASubmission.SIZE_LIMIT_DOCUMENT - 1
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

    @patch.object(telegram, "Bot")
    def test_auto_doc_just_over_size_limit(self, bot):
        post_id = "1234"
        image_id = "5324543"
        thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
        download_link = f"https://d.facdn.net/art/fender/{image_id}/{image_id}.fender_blah-de-blah.pdf"
        full_link = f"{download_link}.jpg"
        submission = FASubmissionFull(post_id, thumb_link, download_link, full_link)
        submission._download_file_size = FASubmission.SIZE_LIMIT_DOCUMENT + 1
        chat_id = -9327622
        message_id = 2873292

        submission.send_message(bot, chat_id, message_id)

        bot.send_photo.assert_called_once()
        bot.send_document.assert_not_called()
        bot.send_message.assert_not_called()
        assert bot.send_photo.call_args[1]['chat_id'] == chat_id
        assert bot.send_photo.call_args[1]['photo'] == submission.full_image_url
        assert bot.send_photo.call_args[1]['caption'] == \
            f"{submission.link}\n[Direct download]({submission.download_url})"
        assert bot.send_photo.call_args[1]['reply_to_message_id'] == message_id
        assert bot.send_photo.call_args[1]['parse_mode'] == telegram.ParseMode.MARKDOWN
