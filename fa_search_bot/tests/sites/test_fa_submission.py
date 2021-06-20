import asyncio

from fa_search_bot.sites.fa_handler import FAHandler
from fa_search_bot.sites.fa_submission import FASubmission, FASubmissionShort, FASubmissionFull
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder

loop = asyncio.get_event_loop()


def test_constructor():
    post_id = "1242"

    submission = FASubmission(post_id)

    assert submission.submission_id == post_id
    assert FAHandler.FA_SUB_LINK.search(submission.link) is not None
    assert f"view/{post_id}" in submission.link


def test_create_from_short_dict():
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


def test_create_from_full_dict():
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


def test_create_short_dict_makes_thumb_bigger_75():
    builder = SubmissionBuilder(thumb_size=75)
    big_thumb_link = builder.thumbnail_url.replace("@75-", "@1600-")

    submission = FASubmission.from_short_dict(
        builder.build_search_json()
    )

    assert submission.thumbnail_url == big_thumb_link


def test_make_thumbnail_bigger():
    post_id = "1234"
    image_id = "5324543"
    thumb_link = f"https://t.furaffinity.net/{post_id}@400-{image_id}.jpg"
    big_thumb_link = f"https://t.furaffinity.net/{post_id}@1600-{image_id}.jpg"

    big_link = FASubmission.make_thumbnail_bigger(thumb_link)

    assert big_link == big_thumb_link


def test_make_thumbnail_bigger__facdn():
    post_id = "1234"
    image_id = "5324543"
    thumb_link = f"https://t.facdn.net/{post_id}@400-{image_id}.jpg"
    big_thumb_link = f"https://t.furaffinity.net/{post_id}@1600-{image_id}.jpg"

    big_link = FASubmission.make_thumbnail_bigger(thumb_link)

    assert big_link == big_thumb_link


def test_make_thumbnail_bigger_size_75():
    post_id = "1234"
    image_id = "5324543"
    # Only available size not ending 0
    thumb_link = f"https://t.furaffinity.net/{post_id}@75-{image_id}.jpg"
    big_thumb_link = f"https://t.furaffinity.net/{post_id}@1600-{image_id}.jpg"

    big_link = FASubmission.make_thumbnail_bigger(thumb_link)

    assert big_link == big_thumb_link


def test_id_from_link():
    post_id = "12874"
    link = f"https://furaffinity.net/view/{post_id}/"

    new_id = FASubmission.id_from_link(link)

    assert new_id == post_id


def test_get_file_size(requests_mock):
    url = "http://example.com/file.jpg"
    size = 7567
    requests_mock.head(
        url,
        headers={
            "content-length": str(size)
        }
    )

    file_size = FASubmission._get_file_size(url)

    assert isinstance(size, int)
    assert file_size == size
