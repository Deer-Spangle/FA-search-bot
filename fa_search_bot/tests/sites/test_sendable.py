from unittest import mock
from unittest.mock import Mock

import pytest
from docker import DockerClient
from telethon.tl.custom import InlineBuilder

from fa_search_bot.sites.fa_handler import SendableFASubmission
from fa_search_bot.sites.fa_submission import FAUser
from fa_search_bot.sites.sendable import Sendable, random_sandbox_video_path
from fa_search_bot.tests.conftest import MockChat
from fa_search_bot.tests.util.mock_method import MockMethod, MockMultiMethod
from fa_search_bot.tests.util.mock_telegram_event import MockInlineMessageId
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder


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
    two_pass_output_path = random_sandbox_video_path()
    mock_run = MockMethod(two_pass_output_path)
    mock_filesize = MockMethod(sendable.SIZE_LIMIT_GIF + 10)
    sendable._convert_two_pass = mock_run.async_call

    with mock.patch("os.path.getsize", mock_filesize.call):
        output_path = await sendable._convert_gif(submission.download_url)

    assert output_path == two_pass_output_path
    assert isinstance(mock_run.args[0], DockerClient)
    assert isinstance(mock_run.args[1], str)
    assert mock_run.args[1].endswith(".mp4")
    assert mock_run.args[2] == submission.download_url
    assert isinstance(mock_run.args[3], str)


@pytest.mark.asyncio
async def test_two_pass():
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    docker_client = DockerClient.from_env()
    sandbox_path = random_sandbox_video_path()
    ffmpeg_options = "--just_testing"
    duration = 27.5
    audio_bitrate = 127000
    mock_run = MockMultiMethod([str(duration), "audio", "127000", "ffmpeg1", "ffmpeg2"])
    sendable._run_docker = mock_run.async_call
    video_bitrate = (sendable.SIZE_LIMIT_VIDEO / 27.5 * 8) - audio_bitrate

    output_path = await sendable._convert_two_pass(docker_client, sandbox_path, submission.download_url, ffmpeg_options)

    assert output_path is not None
    assert output_path.endswith(".mp4")
    assert output_path != sandbox_path
    assert mock_run.calls == 5
    # ffprobe call
    assert mock_run.args[0][1].startswith("-show_entries format=duration ")
    assert mock_run.kwargs[0]["entrypoint"] == "ffprobe"
    # audio stream check
    assert "-show_streams -select_streams a" in mock_run.args[1][1]
    assert mock_run.kwargs[1]["entrypoint"] == "ffprobe"
    # audio bitrate call
    assert "-show_entries stream=bit_rate " in mock_run.args[2][1]
    assert "-select_streams a " in mock_run.args[2][1]
    assert mock_run.kwargs[2]["entrypoint"] == "ffprobe"
    # First ffmpeg two pass call
    assert mock_run.args[3][1].strip().startswith(f"-i {submission.download_url} ")
    assert " -pass 1 -f mp4 " in mock_run.args[3][1]
    assert f" -b:v {video_bitrate} " in mock_run.args[3][1]
    assert mock_run.args[3][1].endswith(" /dev/null -y")
    # Second ffmpeg two pass call
    assert mock_run.args[4][1].strip().startswith(f"-i {submission.download_url} ")
    assert " -pass 2 " in mock_run.args[4][1]
    assert f" -b:v {video_bitrate} " in mock_run.args[4][1]
    assert mock_run.args[4][1].endswith(f" /{output_path} -y")


@pytest.mark.asyncio
async def test_video_has_audio():
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    mock_run = MockMethod("stream 1: some audio")
    sendable._run_docker = mock_run.async_call
    client = DockerClient.from_env()
    video_path = random_sandbox_video_path()

    audio = await sendable._video_has_audio_track(client, video_path)

    assert audio is True
    assert mock_run.called
    assert mock_run.args[0] == client
    assert "-show_streams -select_streams a" in mock_run.args[1]
    assert video_path in mock_run.args[1]
    assert mock_run.kwargs['entrypoint'] == "ffprobe"


@pytest.mark.asyncio
async def test_video_has_no_audio():
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    mock_run = MockMethod("")
    sendable._run_docker = mock_run.async_call
    client = DockerClient.from_env()
    video_path = random_sandbox_video_path()

    audio = await sendable._video_has_audio_track(client, video_path)

    assert audio is False
    assert mock_run.called
    assert mock_run.args[0] == client
    assert "-show_streams -select_streams a" in mock_run.args[1]
    assert video_path in mock_run.args[1]
    assert mock_run.kwargs['entrypoint'] == "ffprobe"


@pytest.mark.asyncio
async def test_convert_video_animated_image():
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    output_gif_path = random_sandbox_video_path()
    mock_run = MockMethod(output_gif_path)
    sendable._convert_gif = mock_run.async_call

    with mock.patch("fa_search_bot.sites.sendable._is_animated", return_value=True):
        output_path = await sendable._convert_video(submission.download_url)

    assert output_path == output_gif_path
    assert mock_run.called
    assert mock_run.args == (submission.download_url,)


@pytest.mark.asyncio
async def test_convert_video_without_audio():
    submission = SubmissionBuilder(file_ext="webm", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    mock_audio = MockMethod(False)
    sendable._video_has_audio_track = mock_audio.async_call
    mock_duration = MockMethod(Sendable.LENGTH_LIMIT_GIF - 3)
    sendable._video_duration = mock_duration.async_call
    output_gif_path = random_sandbox_video_path()
    mock_gif = MockMethod(output_gif_path)
    sendable._convert_gif = mock_gif.async_call

    output_path = await sendable._convert_video(submission.download_url)

    assert output_path == output_gif_path
    assert mock_audio.called
    assert isinstance(mock_audio.args[0], DockerClient)
    assert isinstance(mock_audio.args[1], str)
    assert mock_duration.called
    assert isinstance(mock_duration.args[0], DockerClient)
    assert isinstance(mock_duration.args[1], str)
    assert mock_gif.called
    assert mock_gif.args[0] == submission.download_url


@pytest.mark.asyncio
async def test_convert_video_without_audio_but_long():
    submission = SubmissionBuilder(file_ext="webm", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    mock_audio = MockMethod(False)
    sendable._video_has_audio_track = mock_audio.async_call
    mock_duration = MockMethod(Sendable.LENGTH_LIMIT_GIF + 3)
    sendable._video_duration = mock_duration.async_call
    output_gif_path = random_sandbox_video_path()
    mock_gif = MockMethod(output_gif_path)
    sendable._convert_gif = mock_gif.async_call
    mock_run = MockMethod("")
    sendable._run_docker = mock_run.async_call

    with mock.patch("os.path.getsize", return_value=sendable.SIZE_LIMIT_VIDEO - 10):
        output_path = await sendable._convert_video(submission.download_url)

    assert output_path is not None
    assert output_path != output_gif_path
    assert output_path.endswith(".mp4")
    assert mock_audio.called
    assert isinstance(mock_audio.args[0], DockerClient)
    assert isinstance(mock_audio.args[1], str)
    assert mock_duration.called
    assert isinstance(mock_duration.args[0], DockerClient)
    assert isinstance(mock_duration.args[1], str)
    assert not mock_gif.called
    assert mock_run.called
    assert isinstance(mock_run.args[0], DockerClient)
    assert "-f lavfi -i aevalsrc=0" in mock_run.args[1]
    assert "-qscale:v 0" in mock_run.args[1]
    assert submission.download_url in mock_run.args[1]


@pytest.mark.asyncio
async def test_convert_video():
    submission = SubmissionBuilder(file_ext="webm", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    mock_run = MockMethod("")
    sendable._run_docker = mock_run.async_call
    mock_audio = MockMethod(True)
    sendable._video_has_audio_track = mock_audio.async_call
    output_gif_path = random_sandbox_video_path()
    mock_gif = MockMethod(output_gif_path)
    sendable._convert_gif = mock_gif.async_call

    with mock.patch("os.path.getsize", return_value=sendable.SIZE_LIMIT_VIDEO - 10):
        output_path = await sendable._convert_video(submission.download_url)

    assert output_path is not None
    assert output_path != output_gif_path
    assert output_path.endswith(".mp4")
    assert mock_run.called
    assert isinstance(mock_run.args[0], DockerClient)
    assert "-qscale 0" in mock_run.args[1]
    assert submission.download_url in mock_run.args[1]
    assert mock_audio.called
    assert isinstance(mock_audio.args[0], DockerClient)
    assert isinstance(mock_audio.args[1], str)
    assert not mock_gif.called


@pytest.mark.asyncio
async def test_convert_video__two_pass():
    submission = SubmissionBuilder(file_ext="webm", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    mock_run = MockMethod("")
    sendable._run_docker = mock_run.async_call
    output_two_pass = random_sandbox_video_path()
    mock_two_pass = MockMethod(output_two_pass)
    sendable._convert_two_pass = mock_two_pass.async_call

    with mock.patch("fa_search_bot.sites.sendable._is_animated", return_value=False):
        with mock.patch.object(sendable, "_video_has_audio_track", return_value=True):
            with mock.patch("os.path.getsize", return_value=sendable.SIZE_LIMIT_VIDEO + 10):
                output_path = await sendable._convert_video(submission.download_url)

    assert output_path is not None
    assert output_path == output_two_pass
    assert mock_run.called
    assert isinstance(mock_run.args[0], DockerClient)
    assert "-qscale 0" in mock_run.args[1]
    assert submission.download_url in mock_run.args[1]
    assert mock_two_pass.called
    assert isinstance(mock_two_pass.args[0], DockerClient)
    assert isinstance(mock_two_pass.args[1], str)
    assert mock_two_pass.args[2] == submission.download_url
    assert "-qscale 0" in mock_two_pass.args[3]


@pytest.mark.asyncio
async def test_send_animated_gif_submission(mock_client):
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    chat = MockChat(-9327622)
    message_id = 2873292
    convert = MockMethod("output.mp4")
    sendable._convert_gif = convert.async_call
    mock_rename = MockMethod()

    with mock.patch("os.rename", mock_rename.call):
        with mock.patch("fa_search_bot.sites.sendable._is_animated", return_value=True):
            await sendable.send_message(mock_client, chat, reply_to=message_id)

    cache_dir = f"{sendable.CACHE_DIR}/{sendable.site_id}"
    assert convert.called
    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_rename.called
    assert mock_rename.args[0] == "output.mp4"
    assert mock_rename.args[1] == f"{cache_dir}/{submission.submission_id}.mp4"
    assert mock_client.send_message.call_args[1]['file'] == f"{cache_dir}/{submission.submission_id}.mp4"
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
    mock_exists = MockMethod(True)

    with mock.patch("os.path.exists", mock_exists.call):
        with mock.patch("fa_search_bot.sites.sendable._is_animated", return_value=True):
            await sendable.send_message(mock_client, chat, reply_to=message_id)

    cache_dir = f"{sendable.CACHE_DIR}/{sendable.site_id}"
    assert not convert.called
    mock_client.send_message.assert_called_once()
    assert mock_client.send_message.call_args[1]['entity'] == chat
    assert mock_exists.called
    assert mock_exists.args[0] == f"{cache_dir}/{submission.submission_id}.mp4"
    assert mock_client.send_message.call_args[1]['file'] == f"{cache_dir}/{submission.submission_id}.mp4"
    assert mock_client.send_message.call_args[1]['message'] == submission.link
    assert mock_client.send_message.call_args[1]['reply_to'] == message_id


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
    assert mock_client.send_message.call_args.kwargs['entity'] == chat
    assert mock_client.send_message.call_args.kwargs['file'] == png_output
    assert mock_client.send_message.call_args.kwargs['message'] == submission.link
    assert mock_client.send_message.call_args.kwargs['reply_to'] == message_id


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
    assert mock_client.send_message.call_args.kwargs['entity'] == chat
    assert mock_client.send_message.call_args.kwargs['file'] == submission.download_url
    assert mock_client.send_message.call_args.kwargs['message'] == submission.link
    assert mock_client.send_message.call_args.kwargs['reply_to'] == message_id


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
    assert builder.photo.call_args.kwargs['file'] == sendable.thumbnail_url
    assert sendable.site_id in builder.photo.call_args.kwargs['id']
    assert builder.photo.call_args.kwargs['id'] == f"{sendable.site_id}:{sendable.id}"
    assert builder.photo.call_args.kwargs['text'] == sendable.link
    buttons = builder.photo.call_args.kwargs['buttons']
    assert len(buttons) == 1
    assert "Optimising" in buttons[0].text
    assert buttons[0].data == f"neaten_me:{sendable.site_id}:{sendable.id}".encode()
