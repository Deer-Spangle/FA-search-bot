from unittest import mock

import pytest

from fa_search_bot.sites.fa_handler import SendableFASubmission
from fa_search_bot.sites.fa_submission import FAUser
from fa_search_bot.sites.sendable import Sendable
from fa_search_bot.tests.conftest import MockChat
from fa_search_bot.tests.util.mock_method import MockMethod, MockMultiMethod
from fa_search_bot.tests.util.mock_telegram_event import MockInlineMessageId
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder


@pytest.mark.asyncio
async def test_send_animated_gif_submission(mock_client):
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292
    convert = MockMethod("output.mp4")
    sendable._convert_gif = convert.async_call
    mock_open = mock.mock_open(read_data=b"data")
    mock_rename = MockMethod()

    with mock.patch("fa_search_bot.sites.sendable.open", mock_open):
        with mock.patch("os.rename", mock_rename.call):
            with mock.patch("fa_search_bot.sites.sendable._is_animated", return_value=True):
                await sendable.send_message(mock_client, chat, reply_to=message_id)

    assert convert.called
    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_rename.called
    assert mock_rename.args[0] == "output.mp4"
    assert mock_rename.args[1] == f"{sendable.CACHE_DIR}/{sendable.site_id}/{submission.submission_id}.mp4"
    assert mock_open.call_args[0][0] == f"{sendable.CACHE_DIR}/{sendable.site_id}/{submission.submission_id}.mp4"
    assert mock_open.call_args[0][1] == "rb"
    assert mock_client.send_message.call_args[1]['file'] == mock_open.return_value
    assert mock_client.send_message.call_args[1]['message'] == submission.link
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id


@pytest.mark.asyncio
async def test_send_animated_gif_submission_from_cache(mock_client):
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292
    convert = MockMethod("output.mp4")
    sendable._convert_gif = convert.async_call
    mock_open = mock.mock_open(read_data=b"data")
    mock_exists = MockMethod(True)

    with mock.patch("fa_search_bot.sites.sendable.open", mock_open):
        with mock.patch("os.path.exists", mock_exists.call):
            with mock.patch("fa_search_bot.sites.sendable._is_animated", return_value=True):
                await sendable.send_message(mock_client, chat, reply_to=message_id)

    assert not convert.called
    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_exists.called
    assert mock_exists.args[0] == f"{sendable.CACHE_DIR}/{sendable.site_id}/{submission.submission_id}.mp4"
    assert mock_open.call_args[0][0] == f"{sendable.CACHE_DIR}/{sendable.site_id}/{submission.submission_id}.mp4"
    assert mock_open.call_args[0][1] == "rb"
    assert mock_client.send_message.call_args[1]['file'] == mock_open.return_value
    assert mock_client.send_message.call_args[1]['message'] == submission.link
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id


@pytest.mark.asyncio
async def test_convert_gif():
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    mock_run = MockMethod("Test docker")
    mock_filesize = MockMethod(sendable.SIZE_LIMIT_GIF - 10)
    sendable._run_docker = mock_run.async_call

    with mock.patch("os.path.getsize", mock_filesize.call):
        output_path = await sendable._convert_gif(submission.download_url)

    assert output_path is not None
    assert output_path.endswith(".mp4")
    assert mock_run.called
    assert mock_run.args[1].startswith(f"-i {submission.download_url}")
    assert mock_run.args[1].endswith(f" /{output_path}")


@pytest.mark.asyncio
async def test_convert_gif_two_pass():
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    mock_run = MockMultiMethod(["Test docker", "27.5", "ffmpeg1", "ffmpeg2"])
    mock_filesize = MockMethod(sendable.SIZE_LIMIT_GIF + 10)
    sendable._run_docker = mock_run.async_call

    with mock.patch("os.path.getsize", mock_filesize.call):
        output_path = await sendable._convert_gif(submission.download_url)

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
async def test_send_animated_gif_convert_failure(mock_client):
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292
    sendable._convert_gif = lambda *args: (_ for _ in ()).throw(Exception)

    with mock.patch("fa_search_bot.sites.sendable._is_animated", return_value=True):
        await sendable.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args.kwargs['entity'] == chat
    assert mock_client.send_message.call_args.kwargs['file'] == submission.download_url
    assert mock_client.send_message.call_args.kwargs['message'] == submission.link
    assert mock_client.send_message.call_args.kwargs['reply_to'] == message_id


@pytest.mark.asyncio
async def test_send_pdf_submission(mock_client):
    title = "Example title"
    author = FAUser("A writer", "awriter")
    submission = SubmissionBuilder(file_ext="pdf", file_size=47453, title=title, author=author).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.download_url
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id
    assert mock_client.send_message.call_args[1]['force_document'] is True
    sent_message = mock_client.send_message.call_args[1]['message']
    assert sent_message.endswith(submission.link)
    assert f"\"{title}\"" in sent_message
    assert author.name in sent_message
    assert author.link in sent_message


@pytest.mark.asyncio
async def test_send_mp3_submission(mock_client):
    title = "Example music"
    author = FAUser("A musician", "amusician")
    submission = SubmissionBuilder(file_ext="mp3", file_size=47453, title=title, author=author).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id)

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
async def test_send_unrecognised_submission(mock_client):
    title = "Example title"
    author = FAUser("A writer", "awriter")
    submission = SubmissionBuilder(file_ext="txt", title=title, author=author).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id)

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
async def test_send_image_just_under_size_limit(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=Sendable.SIZE_LIMIT_IMAGE - 1) \
        .build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.download_url
    assert mock_client.send_message.call_args[1]['message'] == submission.link
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id


@pytest.mark.asyncio
async def test_send_image_just_over_size_limit(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=Sendable.SIZE_LIMIT_IMAGE + 1) \
        .build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.thumbnail_url
    assert mock_client.send_message.call_args[1]['message'] == \
           f"{submission.link}\n<a href=\"{submission.download_url}\">Direct download</a>"
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id
    assert mock_client.send_message.call_args[1]['parse_mode'] == 'html'


@pytest.mark.asyncio
async def test_send_image_over_document_size_limit(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=Sendable.SIZE_LIMIT_DOCUMENT + 1) \
        .build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.thumbnail_url
    assert mock_client.send_message.call_args[1]['message'] == \
           f"{submission.link}\n<a href=\"{submission.download_url}\">Direct download</a>"
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id
    assert mock_client.send_message.call_args[1]['parse_mode'] == 'html'


@pytest.mark.asyncio
async def test_send_pdf_just_under_size_limit(mock_client):
    title = "Example title"
    author = FAUser("A writer", "awriter")
    submission = SubmissionBuilder(
        file_ext="pdf",
        file_size=Sendable.SIZE_LIMIT_DOCUMENT - 1,
        title=title,
        author=author
    ).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id)

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
async def test_send_pdf_just_over_size_limit(mock_client):
    title = "Example title"
    author = FAUser("A writer", "awriter")
    submission = SubmissionBuilder(
        file_ext="pdf",
        file_size=Sendable.SIZE_LIMIT_DOCUMENT + 1,
        title=title,
        author=author
    ).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id)

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
    submission = SubmissionBuilder(file_ext="jpg", file_size=Sendable.SIZE_LIMIT_IMAGE - 1) \
        .build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id, prefix="Update on a search")

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.download_url
    assert submission.link in mock_client.send_message.call_args[1]['message']
    assert "Update on a search\n" in mock_client.send_message.call_args[1]['message']
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id


@pytest.mark.asyncio
async def test_send_message__without_prefix(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=Sendable.SIZE_LIMIT_IMAGE - 1) \
        .build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_client.send_message.call_args[1]['file'] == submission.download_url
    assert mock_client.send_message.call_args[1]['message'] == submission.link
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id


@pytest.mark.asyncio
async def test_send_message__edit(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=Sendable.SIZE_LIMIT_IMAGE // 2) \
        .build_full_submission()
    sendable = SendableFASubmission(submission)
    entity = MockInlineMessageId()
    message_id = 2873292

    await sendable.send_message(mock_client, entity, reply_to=message_id, edit=True)

    mock_client.send_message.assert_not_called()
    mock_client.edit_message.assert_called_once()
    assert mock_client.edit_message.call_args[1]['entity'] == entity
    assert mock_client.edit_message.call_args[1]['file'] == submission.download_url
    assert mock_client.edit_message.call_args[1]['message'] == submission.link
    assert mock_client.edit_message.call_args[1]['parse_mode'] == 'html'
    assert 'reply_to' not in mock_client.edit_message.call_args[1]
