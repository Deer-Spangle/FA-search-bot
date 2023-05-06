from unittest import mock
from unittest.mock import Mock

import pytest
from telethon.tl.custom import InlineBuilder

from fa_search_bot.sites.furaffinity.sendable import SendableFASubmission
from fa_search_bot.sites.furaffinity.fa_submission import FAUser
from fa_search_bot.sites.sendable import Sendable, SANDBOX_DIR, _url_to_media, SendSettings, CaptionSettings
from fa_search_bot.tests.conftest import MockChat
from fa_search_bot.tests.util.mock_method import MockMethod
from fa_search_bot.tests.util.mock_telegram_event import MockInlineMessageId
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder


@pytest.mark.asyncio
async def test_send_animated_gif_submission(mock_client):
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292
    output_filename = "output.mp4"
    convert = MockMethod(output_filename)
    sendable._convert_gif = convert.async_call

    with mock.patch("fa_search_bot.sites.sendable._is_animated", return_value=True):
        await sendable.send_message(mock_client, chat, reply_to=message_id)

    assert convert.called
    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]["entity"] == chat
    assert mock_client.send_message.call_args[1]["file"] == output_filename
    assert mock_client.send_message.call_args[1]["message"] == submission.link
    assert mock_client.send_message.call_args[1]["reply_to"] == message_id


@pytest.mark.asyncio
async def test_send_static_gif_convert_to_png(mock_client):
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292
    convert = MockMethod("output.mp4")
    sendable._convert_gif = convert.async_call
    png_output = b"png blah"

    with mock.patch("fa_search_bot.sites.sendable._is_animated", return_value=False):
        with mock.patch("fa_search_bot.sites.sendable._convert_gif_to_png", return_value=png_output):
            await sendable.send_message(mock_client, chat, reply_to=message_id)

    assert not convert.called
    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args.kwargs["entity"] == chat
    assert mock_client.send_message.call_args.kwargs["file"] == png_output
    assert mock_client.send_message.call_args.kwargs["message"] == submission.link
    assert mock_client.send_message.call_args.kwargs["reply_to"] == message_id


@pytest.mark.asyncio
async def test_send_static_png_does_not_convert(mock_client):
    submission = SubmissionBuilder(file_ext="png", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292
    convert = MockMethod("output.mp4")
    sendable._convert_gif = convert.async_call
    png_output = b"png blah"

    with mock.patch("fa_search_bot.sites.sendable._is_animated", return_value=False):
        with mock.patch("fa_search_bot.sites.sendable._convert_gif_to_png", return_value=png_output):
            await sendable.send_message(mock_client, chat, reply_to=message_id)

    assert not convert.called
    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args.kwargs["entity"] == chat
    assert mock_client.send_message.call_args.kwargs["file"].startswith(f"{SANDBOX_DIR}/")
    assert mock_client.send_message.call_args.kwargs["file"].endswith(".png")
    assert mock_client.send_message.call_args.kwargs["message"] == submission.link
    assert mock_client.send_message.call_args.kwargs["reply_to"] == message_id


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
    assert mock_client.send_message.call_args.kwargs["entity"] == chat
    assert mock_client.send_message.call_args.kwargs["file"] == submission.download_url
    assert mock_client.send_message.call_args.kwargs["message"] == submission.link
    assert mock_client.send_message.call_args.kwargs["reply_to"] == message_id


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
    assert mock_client.send_message.call_args[1]["entity"] == chat
    assert mock_client.send_message.call_args[1]["file"] == submission.download_url
    assert mock_client.send_message.call_args[1]["reply_to"] == message_id
    assert mock_client.send_message.call_args[1]["force_document"] is True
    sent_message = mock_client.send_message.call_args[1]["message"]
    assert sent_message.endswith(submission.link)
    assert f'"{title}"' in sent_message
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
    assert mock_client.send_message.call_args[1]["entity"] == chat
    assert mock_client.send_message.call_args[1]["file"] == submission.download_url
    assert mock_client.send_message.call_args[1]["reply_to"] == message_id
    sent_message = mock_client.send_message.call_args[1]["message"]
    assert sent_message.endswith(submission.link)
    assert f'"{title}"' in sent_message
    assert author.name in sent_message
    assert author.link in sent_message


@pytest.mark.asyncio
async def test_send_unrecognised_submission(mock_client):
    title = "Example title"
    author = FAUser("A writer", "awriter")
    submission = SubmissionBuilder(file_ext="txt", title=title, author=author).build_mock_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]["entity"] == chat
    assert mock_client.send_message.call_args[1]["file"] == submission.full_image_url
    assert mock_client.send_message.call_args[1]["reply_to"] == message_id
    assert mock_client.send_message.call_args[1]["parse_mode"] == "html"
    sent_message = mock_client.send_message.call_args[1]["message"]
    assert sent_message.endswith(f'{submission.link}\n<a href="{submission.download_url}">Direct download</a>')
    assert f'"{title}"' in sent_message
    assert author.name in sent_message
    assert author.link in sent_message


@pytest.mark.asyncio
async def test_send_image_just_under_size_limit(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=Sendable.SIZE_LIMIT_IMAGE - 1).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]["entity"] == chat
    assert mock_client.send_message.call_args[1]["file"].startswith(f"{SANDBOX_DIR}/")
    assert mock_client.send_message.call_args[1]["file"].endswith(".jpg")
    assert mock_client.send_message.call_args[1]["message"] == submission.link
    assert mock_client.send_message.call_args[1]["reply_to"] == message_id


@pytest.mark.asyncio
async def test_send_image_just_over_size_limit(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=Sendable.SIZE_LIMIT_IMAGE + 1).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]["entity"] == chat
    assert mock_client.send_message.call_args.kwargs["file"].startswith(f"{SANDBOX_DIR}/")
    assert mock_client.send_message.call_args.kwargs["file"].endswith(".jpg")
    assert (
        mock_client.send_message.call_args[1]["message"]
        == f'{submission.link}\n<a href="{submission.download_url}">Direct download</a>'
    )
    assert mock_client.send_message.call_args[1]["reply_to"] == message_id
    assert mock_client.send_message.call_args[1]["parse_mode"] == "html"


@pytest.mark.asyncio
async def test_send_image_over_document_size_limit(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=Sendable.SIZE_LIMIT_DOCUMENT + 1).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]["entity"] == chat
    assert mock_client.send_message.call_args.kwargs["file"].startswith(f"{SANDBOX_DIR}/")
    assert mock_client.send_message.call_args.kwargs["file"].endswith(".jpg")
    assert (
        mock_client.send_message.call_args[1]["message"]
        == f'{submission.link}\n<a href="{submission.download_url}">Direct download</a>'
    )
    assert mock_client.send_message.call_args[1]["reply_to"] == message_id
    assert mock_client.send_message.call_args[1]["parse_mode"] == "html"


@pytest.mark.asyncio
async def test_send_pdf_just_under_size_limit(mock_client):
    title = "Example title"
    author = FAUser("A writer", "awriter")
    submission = SubmissionBuilder(
        file_ext="pdf",
        file_size=Sendable.SIZE_LIMIT_DOCUMENT - 1,
        title=title,
        author=author,
    ).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]["entity"] == chat
    assert mock_client.send_message.call_args[1]["file"] == submission.download_url
    assert mock_client.send_message.call_args[1]["reply_to"] == message_id
    sent_message = mock_client.send_message.call_args[1]["message"]
    assert sent_message.endswith(submission.link)
    assert f'"{title}"' in sent_message
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
        author=author,
    ).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292

    await sendable.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]["entity"] == chat
    assert mock_client.send_message.call_args[1]["file"] == submission.full_image_url
    assert mock_client.send_message.call_args[1]["reply_to"] == message_id
    assert mock_client.send_message.call_args[1]["parse_mode"] == "html"
    sent_message = mock_client.send_message.call_args[1]["message"]
    assert sent_message.endswith(f'{submission.link}\n<a href="{submission.download_url}">Direct download</a>')
    assert f'"{title}"' in sent_message
    assert author.name in sent_message
    assert author.link in sent_message


@pytest.mark.asyncio
async def test_send_message__calls_upload(mock_client):
    submission = SubmissionBuilder().build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-92343222)
    message_id = 765243
    mock_media = _url_to_media(submission.download_url, True)
    settings = SendSettings(CaptionSettings())

    with mock.patch.object(sendable, "upload", return_value=(mock_media, settings)) as mock_upload:
        await sendable.send_message(mock_client, chat, reply_to=message_id)

    mock_upload.assert_called_once()
    mock_upload.assert_called_with(mock_client)
    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]["entity"] == chat
    assert mock_client.send_message.call_args.kwargs["file"] == mock_media
    assert submission.link in mock_client.send_message.call_args[1]["message"]


@pytest.mark.asyncio
async def test_send_message__with_prefix(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=Sendable.SIZE_LIMIT_IMAGE - 1).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292
    mock_media = _url_to_media(submission.download_url, True)
    settings = SendSettings(CaptionSettings())

    with mock.patch.object(sendable, "upload", return_value=(mock_media, settings)):
        await sendable.send_message(mock_client, chat, reply_to=message_id, prefix="Update on a search")

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]["entity"] == chat
    assert mock_client.send_message.call_args.kwargs["file"] == mock_media
    assert submission.link in mock_client.send_message.call_args[1]["message"]
    assert "Update on a search\n" in mock_client.send_message.call_args[1]["message"]
    assert mock_client.send_message.call_args[1]["reply_to"] == message_id


@pytest.mark.asyncio
async def test_send_message__without_prefix(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=Sendable.SIZE_LIMIT_IMAGE - 1).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292
    mock_media = _url_to_media(submission.download_url, True)
    settings = SendSettings(CaptionSettings())

    with mock.patch.object(sendable, "upload", return_value=(mock_media, settings)):
        await sendable.send_message(mock_client, chat, reply_to=message_id)

    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]["entity"] == chat
    assert mock_client.send_message.call_args.kwargs["file"] == mock_media
    assert mock_client.send_message.call_args[1]["message"] == submission.link
    assert mock_client.send_message.call_args[1]["reply_to"] == message_id


@pytest.mark.asyncio
async def test_send_message__edit(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=Sendable.SIZE_LIMIT_IMAGE // 2).build_full_submission()
    sendable = SendableFASubmission(submission)
    entity = MockInlineMessageId()
    message_id = 2873292
    mock_media = _url_to_media(submission.download_url, True)
    settings = SendSettings(CaptionSettings())

    with mock.patch.object(sendable, "upload", return_value=(mock_media, settings)):
        await sendable.send_message(mock_client, entity, reply_to=message_id, edit=True)

    mock_client.send_message.assert_not_called()
    mock_client.edit_message.assert_called_once()
    assert mock_client.edit_message.call_args.kwargs["entity"] == entity
    assert mock_client.edit_message.call_args.kwargs["file"] == mock_media
    assert mock_client.edit_message.call_args.kwargs["message"] == submission.link
    assert mock_client.edit_message.call_args.kwargs["parse_mode"] == "html"
    assert "reply_to" not in mock_client.edit_message.call_args[1]


@pytest.mark.asyncio
async def test_inline_query():
    submission = SubmissionBuilder().build_full_submission()
    sendable = SendableFASubmission(submission)
    builder = Mock(InlineBuilder)
    exp_result = "expected result"
    builder.photo.return_value = exp_result

    result = await sendable.to_inline_query_result(builder)

    assert result == exp_result
    builder.photo.assert_called_once()
    assert builder.photo.call_args.kwargs["file"] == sendable.thumbnail_url
    assert sendable.site_id in builder.photo.call_args.kwargs["id"]
    assert builder.photo.call_args.kwargs["id"] == f"{sendable.site_id}:{sendable.id}"
    assert builder.photo.call_args.kwargs["text"] == sendable.link
    buttons = builder.photo.call_args.kwargs["buttons"]
    assert len(buttons) == 1
    assert "Optimising" in buttons[0].text
    assert buttons[0].data == f"neaten_me:{sendable.site_id}:{sendable.id}".encode()
