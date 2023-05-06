from unittest import mock
from unittest.mock import Mock

import pytest
from docker import DockerClient

from fa_search_bot.sites.furaffinity.sendable import SendableFASubmission
from fa_search_bot.sites.sendable import Sendable, temp_sandbox_file
from fa_search_bot.tests.util.mock_method import MockMethod, MockMultiMethod
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder


@pytest.mark.asyncio
async def test_convert_gif():
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    mock_run = MockMethod("Test docker")
    mock_filesize = MockMethod(sendable.SIZE_LIMIT_GIF - 10)
    sendable._run_docker = mock_run.async_call

    with mock.patch("os.path.getsize", mock_filesize.call):
        with temp_sandbox_file("mp4") as output_file:
            output_path = await sendable._convert_gif(submission.download_url, output_file)

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
    mock_two_pass = MockMethod(two_pass_output_path)
    mock_run = MockMethod()
    mock_filesize = MockMethod(sendable.SIZE_LIMIT_GIF + 10)
    sendable._convert_two_pass = mock_two_pass.async_call
    sendable._run_docker = mock_run.async_call

    with mock.patch("os.path.getsize", mock_filesize.call):
        output_path = await sendable._convert_gif(submission.download_url)

    assert output_path == two_pass_output_path
    assert isinstance(mock_two_pass.args[0], DockerClient)
    assert isinstance(mock_two_pass.args[1], str)
    assert mock_two_pass.args[1].endswith(".mp4")
    assert mock_two_pass.args[2] == submission.download_url
    assert isinstance(mock_two_pass.args[3], str)


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
    assert mock_run.kwargs["entrypoint"] == "ffprobe"


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
    assert mock_run.kwargs["entrypoint"] == "ffprobe"


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
