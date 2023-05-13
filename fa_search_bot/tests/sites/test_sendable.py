from unittest import mock
from unittest.mock import Mock, PropertyMock

import pytest
from telethon.tl.custom import InlineBuilder
from telethon.tl.types import InputMediaUploadedDocument, DocumentAttributeFilename, DocumentAttributeVideo, \
    InputMediaDocumentExternal, InputMediaUploadedPhoto, DocumentAttributeAudio

from fa_search_bot.sites.furaffinity.sendable import SendableFASubmission
from fa_search_bot.sites.furaffinity.fa_submission import FAUser
from fa_search_bot.sites.sendable import Sendable, SANDBOX_DIR, _url_to_media, SendSettings, CaptionSettings, \
    VideoMetadata, _downloaded_file
from fa_search_bot.tests.conftest import MockChat
from fa_search_bot.tests.util.mock_method import MockMethod
from fa_search_bot.tests.util.mock_telegram_event import MockInlineMessageId
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder


@pytest.mark.asyncio
async def test_upload__animated_gif_submission(mock_client):
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    duration = 13.7
    width, height = 512, 720
    video_metadata = VideoMetadata(
        {"format": {"duration": duration}, "streams": [{"codec_type": "video", "width": width, "height": height}]}
    )
    file_handle = object()
    mock_client.upload_file.return_value = file_handle

    with mock.patch.object(sendable, "_convert_video", return_value=video_metadata) as convert:
        with mock.patch("fa_search_bot.sites.sendable._is_animated", return_value=True):
            media, settings = await sendable.upload(mock_client)

    # Check called functions
    convert.assert_called_once()
    mock_client.upload_file.assert_called_once()
    # Check send settings
    assert isinstance(settings, SendSettings)
    assert settings.caption.direct_link is False
    assert settings.save_cache is True
    assert settings.force_doc is False
    # Check media
    assert isinstance(media, InputMediaUploadedDocument)
    assert media.file == file_handle
    assert media.mime_type == "video/mp4"
    assert media.force_file is False
    assert media.nosound_video is False
    # Check media attributes
    assert len(media.attributes) == 2
    attr_filename = media.attributes[0]
    attr_video = media.attributes[1]
    if not isinstance(attr_filename, DocumentAttributeFilename):
        attr_video = media.attributes[0]
        attr_filename = media.attributes[1]
    assert isinstance(attr_filename, DocumentAttributeFilename)
    assert isinstance(attr_video, DocumentAttributeVideo)
    assert "FASearchBot" in attr_filename.file_name
    assert submission.submission_id in attr_filename.file_name
    assert sendable.site_id in attr_filename.file_name
    assert attr_video.duration == int(duration)
    assert attr_video.w == width
    assert attr_video.h == height


@pytest.mark.asyncio
async def test_upload__animated_gif_convert_failure(mock_client):
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    sendable._convert_video = lambda *args: (_ for _ in ()).throw(Exception)

    with mock.patch.object(
            sendable, "_convert_video", side_effect=lambda *args: (_ for _ in ()).throw(Exception)
    ) as convert:
        with mock.patch("fa_search_bot.sites.sendable._is_animated", return_value=True):
            media, settings = await sendable.upload(mock_client)

    # Check called functions
    convert.assert_called_once()
    mock_client.upload_file.assert_not_called()
    # Check send settings
    assert isinstance(settings, SendSettings)
    assert settings.caption.direct_link is True
    assert settings.save_cache is False
    assert settings.force_doc is False
    # Check media
    assert isinstance(media, InputMediaDocumentExternal)
    assert media.url == submission.download_url


@pytest.mark.asyncio
async def test_upload__webm_submission(mock_client):
    submission = SubmissionBuilder(file_ext="webm", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    duration = 173.5
    width, height = 1280, 1080
    video_metadata = VideoMetadata(
        {"format": {"duration": duration}, "streams": [{"codec_type": "video", "width": width, "height": height}]}
    )
    file_handle = object()
    mock_client.upload_file.return_value = file_handle

    with mock.patch.object(sendable, "_convert_video", return_value=video_metadata) as convert:
        media, settings = await sendable.upload(mock_client)

    # Check called functions
    convert.assert_called_once()
    mock_client.upload_file.assert_called_once()
    # Check send settings
    assert isinstance(settings, SendSettings)
    assert settings.caption.direct_link is False
    assert settings.save_cache is True
    assert settings.force_doc is False
    # Check media
    assert isinstance(media, InputMediaUploadedDocument)
    assert media.file == file_handle
    assert media.mime_type == "video/mp4"
    assert media.force_file is False
    assert media.nosound_video is False
    # Check media attributes
    assert len(media.attributes) == 2
    attr_filename = media.attributes[0]
    attr_video = media.attributes[1]
    if not isinstance(attr_filename, DocumentAttributeFilename):
        attr_video = media.attributes[0]
        attr_filename = media.attributes[1]
    assert isinstance(attr_filename, DocumentAttributeFilename)
    assert isinstance(attr_video, DocumentAttributeVideo)
    assert "FASearchBot" in attr_filename.file_name
    assert submission.submission_id in attr_filename.file_name
    assert sendable.site_id in attr_filename.file_name
    assert attr_video.duration == int(duration)
    assert attr_video.w == width
    assert attr_video.h == height


@pytest.mark.asyncio
async def test_upload__image_static_gif_converted_to_jpg(mock_client):
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    file_handle = object()
    mock_client.upload_file.return_value = file_handle

    with mock.patch("fa_search_bot.sites.sendable._is_animated", return_value=False):
        media, settings = await sendable.upload(mock_client)

    # Check mock calls
    mock_client.upload_file.assert_called_once()
    assert mock_client.upload_file.calls[0].args[0].endswith(".jpg")
    # Check media
    assert isinstance(media, InputMediaUploadedPhoto)
    assert media.file == file_handle
    # Check settings
    assert isinstance(settings, SendSettings)
    assert settings == SendSettings(
        CaptionSettings(
            direct_link=False,
            title=False,
            author=False,
        ),
        force_doc=False,
        save_cache=True,
    )


@pytest.mark.asyncio
async def test_upload__image_static_jpg_does_not_check_animated(mock_client):
    submission = SubmissionBuilder(file_ext="jpg", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    file_handle = object()
    mock_client.upload_file.return_value = file_handle

    with mock.patch("fa_search_bot.sites.sendable._is_animated", return_value=False) as is_animated:
        media, settings = await sendable.upload(mock_client)

    # Check mock calls
    is_animated.assert_not_called()
    mock_client.upload_file.assert_called_once()
    assert mock_client.upload_file.calls[0].args[0].endswith(".jpg")
    # Check media
    assert isinstance(media, InputMediaUploadedPhoto)
    assert media.file == file_handle
    # Check settings
    assert isinstance(settings, SendSettings)
    assert settings == SendSettings(
        CaptionSettings(
            direct_link=False,
            title=False,
            author=False,
        ),
        force_doc=False,
        save_cache=True,
    )


@pytest.mark.asyncio
async def test_upload__image_just_under_size_limit(mock_client):
    submission = SubmissionBuilder(file_ext="jpg").build_full_submission()
    sendable = SendableFASubmission(submission)
    file_handle = object()
    mock_client.upload_file.return_value = file_handle

    with mock.patch("os.path.getsize", return_value=Sendable.SIZE_LIMIT_IMAGE - 1):
        media, settings = await sendable.upload(mock_client)

    # Check mock calls
    mock_client.upload_file.assert_called_once()
    assert mock_client.upload_file.calls[0].args[0].endswith(".jpg")
    # Check media
    assert isinstance(media, InputMediaUploadedPhoto)
    assert media.file == file_handle
    # Check settings
    assert isinstance(settings, SendSettings)
    assert settings == SendSettings(
        CaptionSettings(
            direct_link=False,
            title=False,
            author=False,
        ),
        force_doc=False,
        save_cache=True,
    )


@pytest.mark.asyncio
async def test_upload__image_just_over_size_limit(mock_client):
    submission = SubmissionBuilder(file_ext="jpg").build_full_submission()
    sendable = SendableFASubmission(submission)
    file_handle = object()
    mock_client.upload_file.return_value = file_handle

    with mock.patch("os.path.getsize", return_value=Sendable.SIZE_LIMIT_IMAGE + 1):
        media, settings = await sendable.upload(mock_client)

    # Check mock calls
    mock_client.upload_file.assert_called_once()
    assert mock_client.upload_file.calls[0].args[0].endswith(".jpg")
    # Check media
    assert isinstance(media, InputMediaUploadedPhoto)
    assert media.file == file_handle
    # Check settings
    assert isinstance(settings, SendSettings)
    assert settings == SendSettings(
        CaptionSettings(
            direct_link=True,
            title=False,
            author=False,
        ),
        force_doc=False,
        save_cache=True,
    )


@pytest.mark.asyncio
async def test_upload__image_just_over_semiperimeter(mock_client):
    submission = SubmissionBuilder(file_ext="jpg").build_full_submission()
    sendable = SendableFASubmission(submission)
    file_handle = object()
    mock_client.upload_file.return_value = file_handle
    width, height = Sendable.SEMIPERIMETER_LIMIT_IMAGE // 2 + 1, Sendable.SEMIPERIMETER_LIMIT_IMAGE // 2 + 1

    with mock.patch("fa_search_bot.sites.sendable._img_size", return_value=(width, height)):
        media, settings = await sendable.upload(mock_client)

    # Check mock calls
    mock_client.upload_file.assert_called_once()
    assert mock_client.upload_file.calls[0].args[0].endswith(".jpg")
    # Check media
    assert isinstance(media, InputMediaUploadedPhoto)
    assert media.file == file_handle
    # Check settings
    assert isinstance(settings, SendSettings)
    assert settings == SendSettings(
        CaptionSettings(
            direct_link=True,
            title=False,
            author=False,
        ),
        force_doc=False,
        save_cache=True,
    )


@pytest.mark.asyncio
async def test_upload__image_has_transparency(mock_client):
    submission = SubmissionBuilder(file_ext="jpg").build_full_submission()
    sendable = SendableFASubmission(submission)
    file_handle = object()
    mock_client.upload_file.return_value = file_handle

    with mock.patch("fa_search_bot.sites.sendable._img_has_transparency", return_value=True):
        media, settings = await sendable.upload(mock_client)

    # Check mock calls
    mock_client.upload_file.assert_called_once()
    assert mock_client.upload_file.calls[0].args[0].endswith(".jpg")
    # Check media
    assert isinstance(media, InputMediaUploadedPhoto)
    assert media.file == file_handle
    # Check settings
    assert isinstance(settings, SendSettings)
    assert settings == SendSettings(
        CaptionSettings(
            direct_link=True,
            title=False,
            author=False,
        ),
        force_doc=False,
        save_cache=True,
    )


@pytest.mark.asyncio
async def test_upload__pdf_just_under_size_limit(mock_client):
    title = "Example title"
    author = FAUser("A writer", "awriter")
    submission = SubmissionBuilder(
        file_ext="pdf",
        file_size=Sendable.SIZE_LIMIT_DOCUMENT - 1,
        title=title,
        author=author,
    ).build_full_submission()
    sendable = SendableFASubmission(submission)

    media, settings = await sendable.upload(mock_client)

    assert isinstance(media, InputMediaDocumentExternal)
    assert media.url == submission.download_url
    assert isinstance(settings, SendSettings)
    assert settings == SendSettings(
        CaptionSettings(
            direct_link=False,
            author=True,
            title=True,
        ),
        force_doc=True,
        save_cache=True,
    )


@pytest.mark.asyncio
async def test_upload__pdf_just_over_size_limit(mock_client):
    title = "Example title"
    author = FAUser("A writer", "awriter")
    submission = SubmissionBuilder(
        file_ext="pdf",
        file_size=Sendable.SIZE_LIMIT_DOCUMENT + 1,
        title=title,
        author=author,
    ).build_full_submission()
    sendable = SendableFASubmission(submission)
    file_handle = object()
    mock_client.upload_file.return_value = file_handle

    media, settings = await sendable.upload(mock_client)

    assert isinstance(media, InputMediaUploadedPhoto)
    assert media.file == file_handle
    assert isinstance(settings, SendSettings)
    assert settings == SendSettings(
        CaptionSettings(
            direct_link=True,
            author=True,
            title=True,
        ),
        force_doc=False,
        save_cache=True,
    )


@pytest.mark.asyncio
async def test_upload__mp3_submission(mock_client):
    title = "Example music"
    author = FAUser("A musician", "amusician")
    submission = SubmissionBuilder(file_ext="mp3", file_size=47453, title=title, author=author).build_full_submission()
    sendable = SendableFASubmission(submission)
    file_handle = object()
    mock_client.upload_file.return_value = file_handle

    media, settings = await sendable.upload(mock_client)

    # Check media
    assert isinstance(media, InputMediaUploadedDocument)
    assert media.file == file_handle
    assert len(media.attributes) == 2
    attr_filename = media.attributes[0]
    attr_audio = media.attributes[1]
    if not isinstance(attr_filename, DocumentAttributeFilename):
        attr_audio = media.attributes[0]
        attr_filename = media.attributes[1]
    assert isinstance(attr_filename, DocumentAttributeFilename)
    assert "FASearchBot" in attr_filename.file_name
    assert sendable.site_id in attr_filename.file_name
    assert submission.submission_id in attr_filename.file_name
    assert isinstance(attr_audio, DocumentAttributeAudio)
    assert attr_audio.title == sendable.title
    assert attr_audio.performer == sendable.author
    # Check settings
    assert isinstance(settings, SendSettings)
    assert settings == SendSettings(
        CaptionSettings(
            direct_link=False,
            title=True,
            author=True,
        ),
        force_doc=False,
        save_cache=True,
    )


@pytest.mark.asyncio
async def test_upload__unrecognised_submission(mock_client):
    title = "Example title"
    author = FAUser("A writer", "awriter")
    submission = SubmissionBuilder(file_ext="txt", title=title, author=author).build_mock_submission()
    sendable = SendableFASubmission(submission)
    file_handle = object()
    mock_client.upload_file.return_value = file_handle

    with mock.patch("fa_search_bot.sites.sendable._downloaded_file", wraps=_downloaded_file) as mock_dl:
        media, settings = await sendable.upload(mock_client)

    # Check preview is downloaded
    mock_dl.assert_called_once()
    mock_dl.assert_called_with(sendable.preview_image_url)
    # Check media
    assert isinstance(media, InputMediaUploadedPhoto)
    assert media.file == file_handle
    # TODO: Check it was from preview image
    assert isinstance(settings, SendSettings)
    assert settings == SendSettings(
        CaptionSettings(
            direct_link=True,
            title=True,
            author=True,
        ),
        force_doc=False,
        save_cache=True,
    )


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
