import unittest
from unittest.mock import Mock

from telethon.tl.custom import InlineBuilder

from fa_search_bot.sites.furaffinity.fa_submission import FASubmissionShort, FAUser


class FASubmissionShortTest(unittest.TestCase):
    def test_constructor(self):
        post_id = "1234"
        image_id = "5324543"
        link = f"https://furaffinity.net/view/{post_id}/"
        thumb_link = f"https://t.furaffinity.net/{post_id}@400-{image_id}.jpg"
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
        thumb_url = f"https://t.furaffinity.net/{post_id}@1600-{image_id}.jpg"
        title = "Example post"
        author = FAUser.from_short_dict({"name": "John", "profile_name": "john"})
        submission = FASubmissionShort(post_id, thumb_url, title, author)
        mock_builder = Mock(InlineBuilder)

        submission.to_inline_query_result(mock_builder)

        assert mock_builder.photo.call_args[1]["file"] == thumb_url
        assert mock_builder.photo.call_args[1]["id"] == post_id
        assert mock_builder.photo.call_args[1]["text"] == link
        assert len(mock_builder.photo.call_args[1]["buttons"]) == 1
        assert mock_builder.photo.call_args[1]["buttons"][0].data == f"neaten_me:{post_id}".encode()
