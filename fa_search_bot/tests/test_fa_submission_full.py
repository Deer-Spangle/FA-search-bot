from unittest import mock

import pytest

from fa_search_bot.sites import fa_submission
from fa_search_bot.sites.fa_submission import FAUser, Rating, FASubmissionFull, CantSendFileType, FASubmission
from fa_search_bot.tests.conftest import MockChat
from fa_search_bot.tests.util.mock_method import MockMethod, MockMultiMethod
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder


def test_constructor():
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


def test_download_file_size(requests_mock):
    submission = SubmissionBuilder().build_full_submission()
    size = 23124
    requests_mock.head(
        submission.full_image_url,
        headers={
            "content-length": str(size)
        }
    )

    file_size = submission.download_file_size

    assert isinstance(file_size, int)
    assert file_size == size

    requests_mock.head(
        submission.full_image_url,
        status_code=404
    )

    file_size2 = submission.download_file_size

    assert isinstance(file_size2, int)
    assert file_size2 == size


@pytest.mark.asyncio
async def test_gif_submission(mock_client):
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    chat = MockChat(-9327622)
    message_id = 2873292
    convert = MockMethod("output.mp4")
    submission._convert_gif = convert.async_call
    mock_open = mock.mock_open(read_data=b"data")
    mock_rename = MockMethod()

    with mock.patch("fa_search_bot.sites.fa_submission.open", mock_open):
        with mock.patch("os.rename", mock_rename.call):
            await submission.send_message(mock_client, chat, reply_to=message_id)

    assert convert.called
    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_rename.called
    assert mock_rename.args[0] == "output.mp4"
    assert mock_rename.args[1] == f"{submission.GIF_CACHE_DIR}/{submission.submission_id}.mp4"
    assert mock_open.call_args[0][0] == f"{submission.GIF_CACHE_DIR}/{submission.submission_id}.mp4"
    assert mock_open.call_args[0][1] == "rb"
    assert mock_client.send_message.call_args[1]['file'] == mock_open.return_value
    assert mock_client.send_message.call_args[1]['message'] == submission.link
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id


@pytest.mark.asyncio
async def test_gif_submission_from_cache(mock_client):
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    chat = MockChat(-9327622)
    message_id = 2873292
    convert = MockMethod("output.mp4")
    submission._convert_gif = convert.async_call
    mock_open = mock.mock_open(read_data=b"data")
    mock_exists = MockMethod(True)

    with mock.patch("fa_search_bot.sites.fa_submission.open", mock_open):
        with mock.patch("os.path.exists", mock_exists.call):
            await submission.send_message(mock_client, chat, reply_to=message_id)

    assert not convert.called
    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_exists.called
    assert mock_exists.args[0] == f"{submission.GIF_CACHE_DIR}/{submission.submission_id}.mp4"
    assert mock_open.call_args[0][0] == f"{submission.GIF_CACHE_DIR}/{submission.submission_id}.mp4"
    assert mock_open.call_args[0][1] == "rb"
    assert mock_client.send_message.call_args[1]['file'] == mock_open.return_value
    assert mock_client.send_message.call_args[1]['message'] == submission.link
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id


@pytest.mark.asyncio
async def test_convert_gif():
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    mock_run = MockMethod("Test docker")
    mock_filesize = MockMethod(submission.SIZE_LIMIT_GIF - 10)
    submission._run_docker = mock_run.async_call

    with mock.patch("os.path.getsize", mock_filesize.call):
        output_path = await submission._convert_gif(submission.download_url)

    assert output_path is not None
    assert output_path.endswith(".mp4")
    assert mock_run.called
    assert mock_run.args[1].startswith(f"-i {submission.download_url}")
    assert mock_run.args[1].endswith(f" /{output_path}")


@pytest.mark.asyncio
async def test_convert_gif_two_pass():
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    mock_run = MockMultiMethod(["Test docker", "27.5", "ffmpeg1", "ffmpeg2"])
    mock_filesize = MockMethod(submission.SIZE_LIMIT_GIF + 10)
    submission._run_docker = mock_run.async_call

    with mock.patch("os.path.getsize", mock_filesize.call):
        output_path = await submission._convert_gif(submission.download_url)

    assert output_path is not None
    assert output_path.endswith(".mp4")
    assert mock_run.calls == 4
    # Initial ffmpeg call
    assert mock_run.args[0][1].startswith(f"-i {submission.download_url} ")
    # ffprobe call
    assert mock_run.args[1][1].startswith("-show_entries format=duration ")
    assert mock_run.kwargs[1]["entrypoint"] == "ffprobe"
    # First ffmpeg two pass call
    assert mock_run.args[2][1].startswith(f"-i {submission.download_url} ")
    assert " -pass 1 -f mp4 " in mock_run.args[2][1]
    assert mock_run.args[2][1].endswith(" /dev/null -y")
    # Second ffmpeg two pass call
    assert mock_run.args[3][1].startswith(f"-i {submission.download_url} ")
    assert " -pass 2 " in mock_run.args[3][1]
    assert mock_run.args[3][1].endswith(f" {output_path} -y")


@pytest.mark.asyncio
async def test_convert_gif_failure(mock_client):
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    chat = MockChat(-9327622)
    message_id = 2873292
    submission._convert_gif = lambda *args: (_ for _ in ()).throw(Exception)
    mock_bytes = b"hello world"

    with mock.patch.object(fa_submission, "_convert_gif_to_png", return_value=mock_bytes) as mock_convert:
        await submission.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == mock_bytes
    assert mock_client.send_message.call_args[1]['message'] == submission.link
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id
    mock_convert.assert_called_once()
    assert mock_convert.call_args[0][0] == submission.download_url


@pytest.mark.asyncio
async def test_pdf_submission(mock_client):
    title = "Example title"
    author = FAUser("A writer", "awriter")
    submission = SubmissionBuilder(file_ext="pdf", file_size=47453, title=title, author=author).build_full_submission()
    chat = MockChat(-9327622)
    message_id = 2873292

    await submission.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.download_url
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id
    sent_message = mock_client.send_message.call_args[1]['message']
    assert sent_message.endswith(submission.link)
    assert f"\"{title}\"" in sent_message
    assert author.name in sent_message
    assert author.link in sent_message


@pytest.mark.asyncio
async def test_mp3_submission(mock_client):
    title = "Example music"
    author = FAUser("A musician", "amusician")
    submission = SubmissionBuilder(file_ext="mp3", file_size=47453, title=title, author=author).build_full_submission()
    chat = MockChat(-9327622)
    message_id = 2873292

    await submission.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.download_url
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id
    sent_message = mock_client.send_message.call_args[1]['message']
    assert sent_message.endswith(submission.link)
    assert f"\"{title}\"" in sent_message
    assert author.name in sent_message
    assert author.link in sent_message


@pytest.mark.asyncio
async def test_txt_submission(mock_client):
    title = "Example title"
    author = FAUser("A writer", "awriter")
    submission = SubmissionBuilder(file_ext="txt", title=title, author=author).build_full_submission()
    chat = MockChat(-9327622)
    message_id = 2873292

    await submission.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.full_image_url
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id
    assert mock_client.send_message.call_args[1]['parse_mode'] == 'html'
    sent_message = mock_client.send_message.call_args[1]['message']
    assert sent_message.endswith(f"{submission.link}\n<a href=\"{submission.download_url}\">Direct download</a>")
    assert f"\"{title}\"" in sent_message
    assert author.name in sent_message
    assert author.link in sent_message


@pytest.mark.asyncio
async def test_swf_submission(mock_client):
    submission = SubmissionBuilder(file_ext="swf", file_size=47453).build_full_submission()
    chat = MockChat(-9327622)
    message_id = 2873292

    try:
        await submission.send_message(mock_client, chat, reply_to=message_id)
        assert False, "Should have thrown exception."
    except CantSendFileType as e:
        assert str(e) == "I'm sorry, I can't neaten \".swf\" files."


@pytest.mark.asyncio
async def test_unknown_type_submission(mock_client):
    submission = SubmissionBuilder(file_ext="zzz", file_size=47453).build_full_submission()
    chat = MockChat(-9327622)
    message_id = 2873292

    try:
        await submission.send_message(mock_client, chat, reply_to=message_id)
        assert False, "Should have thrown exception."
    except CantSendFileType as e:
        assert str(e) == "I'm sorry, I don't understand that file extension (zzz)."


@pytest.mark.asyncio
async def test_image_just_under_size_limit(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=FASubmission.SIZE_LIMIT_IMAGE - 1) \
        .build_full_submission()
    chat = MockChat(-9327622)
    message_id = 2873292

    await submission.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.download_url
    assert mock_client.send_message.call_args[1]['message'] == submission.link
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id


@pytest.mark.asyncio
async def test_image_just_over_size_limit(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=FASubmission.SIZE_LIMIT_IMAGE + 1) \
        .build_full_submission()
    chat = MockChat(-9327622)
    message_id = 2873292

    await submission.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.thumbnail_url
    assert mock_client.send_message.call_args[1]['message'] == \
           f"{submission.link}\n<a href=\"{submission.download_url}\">Direct download</a>"
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id
    assert mock_client.send_message.call_args[1]['parse_mode'] == 'html'


@pytest.mark.asyncio
async def test_image_over_document_size_limit(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=FASubmission.SIZE_LIMIT_DOCUMENT + 1) \
        .build_full_submission()
    chat = MockChat(-9327622)
    message_id = 2873292

    await submission.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.thumbnail_url
    assert mock_client.send_message.call_args[1]['message'] == \
           f"{submission.link}\n<a href=\"{submission.download_url}\">Direct download</a>"
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id
    assert mock_client.send_message.call_args[1]['parse_mode'] == 'html'


@pytest.mark.asyncio
async def test_auto_doc_just_under_size_limit(mock_client):
    title = "Example title"
    author = FAUser("A writer", "awriter")
    submission = SubmissionBuilder(
        file_ext="pdf",
        file_size=FASubmission.SIZE_LIMIT_DOCUMENT - 1,
        title=title,
        author=author
    ).build_full_submission()
    chat = MockChat(-9327622)
    message_id = 2873292

    await submission.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.download_url
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id
    sent_message = mock_client.send_message.call_args[1]['message']
    assert sent_message.endswith(submission.link)
    assert f"\"{title}\"" in sent_message
    assert author.name in sent_message
    assert author.link in sent_message


@pytest.mark.asyncio
async def test_auto_doc_just_over_size_limit(mock_client):
    title = "Example title"
    author = FAUser("A writer", "awriter")
    submission = SubmissionBuilder(
        file_ext="pdf",
        file_size=FASubmission.SIZE_LIMIT_DOCUMENT + 1,
        title=title,
        author=author
    ).build_full_submission()
    chat = MockChat(-9327622)
    message_id = 2873292

    await submission.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.full_image_url
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id
    assert mock_client.send_message.call_args[1]['parse_mode'] == 'html'
    sent_message = mock_client.send_message.call_args[1]['message']
    assert sent_message.endswith(f"{submission.link}\n<a href=\"{submission.download_url}\">Direct download</a>")
    assert f"\"{title}\"" in sent_message
    assert author.name in sent_message
    assert author.link in sent_message


@pytest.mark.asyncio
async def test_send_message__with_prefix(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=FASubmission.SIZE_LIMIT_IMAGE - 1) \
        .build_full_submission()
    chat = MockChat(-9327622)
    message_id = 2873292

    await submission.send_message(mock_client, chat, reply_to=message_id, prefix="Update on a search")

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.download_url
    assert submission.link in mock_client.send_message.call_args[1]['message']
    assert "Update on a search\n" in mock_client.send_message.call_args[1]['message']
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id


@pytest.mark.asyncio
async def test_send_message__without_prefix(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=FASubmission.SIZE_LIMIT_IMAGE - 1) \
        .build_full_submission()
    chat = MockChat(-9327622)
    message_id = 2873292

    await submission.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.download_url
    assert mock_client.send_message.call_args[1]['message'] == submission.link
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id
