import abc
import json
from typing import Type, List
from unittest import mock
from unittest.mock import Mock

import pytest
from docker import DockerClient

from fa_search_bot.sites.furaffinity.sendable import SendableFASubmission
from fa_search_bot.sites.sendable import Sendable, temp_sandbox_file, VideoMetadata
from fa_search_bot.tests.util.call_arg_checks import CallArgInstanceOf, CallArgContains
from fa_search_bot.tests.util.mock_method import MockMethod, MockMultiMethod
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder


@pytest.mark.asyncio
async def test_convert_gif():
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    input_path = "sandbox/input_gif_file.gif"
    mock_run = MockMethod("Test docker")
    sendable._run_docker = mock_run.async_call
    video_metadata = object()

    with mock.patch.object(sendable, "_video_metadata", return_value=video_metadata):
        with mock.patch("os.path.getsize", return_value=sendable.SIZE_LIMIT_GIF - 10):
            with temp_sandbox_file("mp4") as output_file:
                output_metadata = await sendable._convert_gif(input_path, output_file)

    assert output_metadata is video_metadata
    assert mock_run.called
    assert mock_run.args[1].startswith(f"-i /{input_path}")
    assert mock_run.args[1].endswith(f" /{output_file}")


@pytest.mark.asyncio
async def test_convert_gif_two_pass():
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    input_path = "sandbox/input_gif.gif"
    output_path = "sandbox/final_output.mp4"
    video_metadata = object()
    two_pass_metadata = object()

    with mock.patch.object(sendable, "_video_metadata", return_value=video_metadata):
        with mock.patch.object(sendable, "_convert_two_pass", return_value=two_pass_metadata) as mock_two_pass:
            with mock.patch.object(sendable, "_run_docker"):
                with mock.patch("os.path.getsize", return_value=sendable.SIZE_LIMIT_GIF + 10):
                    metadata = await sendable._convert_gif(input_path, output_path)

    assert metadata is two_pass_metadata
    assert isinstance(mock_two_pass.call_args[0][0], DockerClient)
    assert mock_two_pass.call_args[0][1] == input_path
    assert mock_two_pass.call_args[0][2] == output_path
    assert mock_two_pass.call_args[0][3] is video_metadata
    assert isinstance(mock_two_pass.call_args[0][4], str)


@pytest.mark.asyncio
async def test_two_pass():
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    docker_client = DockerClient.from_env()
    ffmpeg_options = "--just_testing"
    input_path = "sandbox/input_path.gif"
    output_path = "sandbox/output_path.mp4"
    duration = 27.5
    audio_bitrate = 127000
    video_bitrate = (sendable.SIZE_LIMIT_VIDEO / 27.5 * 8) - audio_bitrate
    video_metadata = object()
    run_return_vals = ["ffmpeg1", "ffmpeg2"]
    input_metadata = VideoMetadata(
        {
            "format": {"duration": duration},
            "streams": [
                {"codec_type": "video", "width": 1280, "height": 720},
                {"codec_type": "audio", "bit_rate": 127000},
            ]
        }
    )

    with mock.patch.object(sendable, "_video_metadata", return_value=video_metadata) as mock_metadata:
        with mock.patch.object(sendable, "_run_docker", side_effect=run_return_vals) as mock_run:
            with mock.patch("shutil.copyfileobj") as mock_copy:
                with mock.patch("builtins.open") as mock_open:
                    metadata = await sendable._convert_two_pass(
                        docker_client, input_path, output_path, input_metadata, ffmpeg_options
                    )

    assert metadata is video_metadata
    # Check metadata calls
    mock_metadata.assert_called_once()
    mock_metadata.assert_called_with(docker_client, output_path)
    # Check docker run calls
    assert mock_run.call_count == 2
    # First ffmpeg two pass call
    first_call = mock_run.call_args_list[0].args
    assert first_call[0] == docker_client
    assert first_call[1].strip().startswith(f"-i /{input_path} ")
    assert " -pass 1 -f mp4 " in first_call[1]
    assert f" -b:v {video_bitrate} " in first_call[1]
    assert first_call[1].endswith(" /dev/null -y")
    # Second ffmpeg two pass call
    second_call = mock_run.call_args_list[1].args
    assert second_call[0] == docker_client
    assert second_call[1].strip().startswith(f"-i /{input_path} ")
    assert " -pass 2 " in second_call[1]
    assert f" -b:v {video_bitrate} " in second_call[1]
    assert second_call[1].endswith(f".mp4 -y")
    # Check open and copy calls
    mock_open.assert_any_call(output_path, "wb")
    mock_copy.assert_called_once()


@pytest.mark.asyncio
async def test_convert_video_animated_image():
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    input_path = "sandbox/input_gif.gif"
    output_path = "sandbox/output_file.mp4"
    mock_run = MockMethod(output_path)
    sendable._convert_gif = mock_run.async_call
    output_metadata = object()

    with mock.patch.object(sendable, "_convert_gif", return_value=output_metadata) as mock_gif:
        metadata = await sendable._convert_video(input_path, output_path)

    mock_gif.assert_called_once()
    mock_gif.assert_called_once_with(input_path, output_path)
    assert metadata is output_metadata


@pytest.mark.asyncio
async def test_convert_video_without_audio():
    submission = SubmissionBuilder(file_ext="webm", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    input_path = "sandbox/input.webm"
    output_path = "sandbox/output_path.mp4"
    output_metadata = object()
    no_audio_metadata = VideoMetadata(
        {
            "format": {"duration": Sendable.LENGTH_LIMIT_GIF - 3},
            "streams": [
                {"codec_type": "video", "width": 1280, "height": 720},
            ]
        }
    )

    with mock.patch.object(sendable, "_convert_gif", return_value=output_metadata) as mock_gif:
        with mock.patch.object(sendable, "_video_metadata", return_value=no_audio_metadata) as mock_metadata:
            metadata = await sendable._convert_video(input_path, output_path)

    assert metadata is output_metadata
    # Check metadata calls
    mock_metadata.assert_called_once()
    mock_metadata.assert_awaited_once_with(mock.ANY, input_path)
    assert isinstance(mock_metadata.call_args.args[0], DockerClient)
    # Check convert gif calls
    mock_gif.assert_called_once()
    mock_gif.assert_called_once_with(input_path, output_path)


@pytest.mark.asyncio
async def test_convert_video_without_audio_but_long():
    submission = SubmissionBuilder(file_ext="webm", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    input_path = "sandbox/input.webm"
    output_path = "sandbox/output_path.mp4"
    no_audio_metadata = VideoMetadata(
        {
            "format": {"duration": Sendable.LENGTH_LIMIT_GIF + 3},
            "streams": [
                {"codec_type": "video", "width": 1280, "height": 720},
            ]
        }
    )
    audio_metadata = VideoMetadata(
        {
            "format": {"duration": Sendable.LENGTH_LIMIT_GIF + 3},
            "streams": [
                {"codec_type": "video", "width": 1280, "height": 720},
                {"codec_type": "audio", "bit_rate": 1000},
            ]
        }
    )
    metadata_resps = [no_audio_metadata, audio_metadata]

    with mock.patch.object(sendable, "_convert_gif") as mock_gif:
        with mock.patch.object(sendable, "_video_metadata", side_effect=metadata_resps) as mock_metadata:
            with mock.patch.object(sendable, "_run_docker") as mock_docker:
                with mock.patch("os.path.getsize", return_value=sendable.SIZE_LIMIT_VIDEO - 10):
                    metadata = await sendable._convert_video(input_path, output_path)

    assert metadata is audio_metadata
    # Check convert gif is not called
    mock_gif.assert_not_called()
    # Check metadata is called
    mock_metadata.assert_called()
    assert mock_metadata.call_count == 2
    # Check docker is called
    mock_docker.assert_called_once()
    assert isinstance(mock_docker.call_args.args[0], DockerClient)
    assert "-f lavfi -i aevalsrc=0" in mock_docker.call_args.args[1]
    assert "-qscale:v 0" in mock_docker.call_args.args[1]
    assert input_path in mock_docker.call_args.args[1]


@pytest.mark.asyncio
async def test_convert_video():
    submission = SubmissionBuilder(file_ext="webm", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    input_path = "sandbox/input_dl.webm"
    output_path = "sandbox/output.mp4"
    output_metadata = VideoMetadata(
        {
            "format": {"duration": Sendable.LENGTH_LIMIT_GIF + 3},
            "streams": [
                {"codec_type": "video", "width": 1280, "height": 720},
                {"codec_type": "audio", "bit_rate": 1000},
            ]
        }
    )

    with mock.patch.object(sendable, "_video_metadata", return_value=output_metadata) as mock_metadata:
        with mock.patch.object(sendable, "_run_docker", return_value="") as mock_run:
            with mock.patch.object(sendable, "_convert_gif", return_value=output_path) as mock_gif:
                with mock.patch("os.path.getsize", return_value=sendable.SIZE_LIMIT_VIDEO - 10):
                    metadata = await sendable._convert_video(input_path, output_path)

    assert metadata is output_metadata
    # Check metadata calls
    assert mock_metadata.call_count == 2
    first_call = mock_metadata.call_args_list[0].args
    assert isinstance(first_call[0], DockerClient)
    assert first_call[1] == input_path
    second_call = mock_metadata.call_args_list[1].args
    assert isinstance(second_call[0], DockerClient)
    assert second_call[1] == output_path
    # Check gif was not called
    mock_gif.assert_not_called()
    # Check docker calls
    mock_run.assert_called_once()
    assert isinstance(mock_run.call_args.args[0], DockerClient)
    assert "-qscale 0" in mock_run.call_args.args[1]
    assert f"/{input_path}" in mock_run.call_args.args[1]


@pytest.mark.asyncio
async def test_convert_video__two_pass():
    submission = SubmissionBuilder(file_ext="webm", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    input_path = "sandbox/input_dl.webm"
    output_path = "sandbox/output.mp4"
    video_metadata = VideoMetadata(
        {
            "format": {"duration": Sendable.LENGTH_LIMIT_GIF + 3},
            "streams": [
                {"codec_type": "video", "width": 1280, "height": 720},
                {"codec_type": "audio", "bit_rate": 1000},
            ]
        }
    )
    output_metadata = object()

    with mock.patch.object(sendable, "_video_metadata", return_value=video_metadata) as mock_metadata:
        with mock.patch.object(sendable, "_run_docker", return_value="") as mock_run:
            with mock.patch.object(sendable, "_convert_gif", return_value=output_path) as mock_gif:
                with mock.patch.object(sendable, "_convert_two_pass", return_value=output_metadata) as mock_two_pass:
                    with mock.patch("os.path.getsize", return_value=sendable.SIZE_LIMIT_VIDEO + 10):
                        metadata = await sendable._convert_video(input_path, output_path)

    assert metadata is output_metadata
    # Check metadata is called once
    mock_metadata.assert_called_once_with(CallArgInstanceOf(DockerClient), input_path)
    # Check docker run is attempted
    mock_run.assert_called_once_with(
        CallArgInstanceOf(DockerClient),
        CallArgContains("-qscale 0") & CallArgContains(f"/{input_path}")
    )
    # Check gif is not called
    mock_gif.assert_not_called()
    # Check two pass is called
    mock_two_pass.assert_called_once()
    mock_two_pass.assert_called_once_with(
        CallArgInstanceOf(DockerClient),
        input_path,
        output_path,
        video_metadata,
        CallArgInstanceOf(str) & CallArgContains("-qscale 0"),
        "",
    )


@pytest.mark.asyncio
async def test_video_metadata():
    submission = SubmissionBuilder(file_ext="gif", file_size=47453).build_full_submission()
    sendable = SendableFASubmission(submission)
    client = DockerClient.from_env()
    input_path = "sandbox/input_metadata_test.mp4"
    duration = 127.5
    width, height = 514, 512
    audio_bitrate = 167000
    metadata_dict = {
        "format": {"duration": duration},
        "streams": [
            {"codec_type": "video", "height": height, "width": width},
            {"codec_type": "audio", "bit_rate": audio_bitrate},
        ]
    }

    with mock.patch.object(sendable, "_run_docker", return_value=json.dumps(metadata_dict)) as mock_run:
        metadata = await sendable._video_metadata(client, input_path)

    mock_run.assert_called_once_with(
        client,
        (
                CallArgContains("format=duration:stream=width,height,bit_rate,codec_type")
                & CallArgContains(f"/{input_path}")
                & CallArgContains("-of json")
        ),
        entrypoint="ffprobe",
    )
    assert isinstance(metadata, VideoMetadata)
    assert metadata.duration == duration
    assert metadata.width == width
    assert metadata.height == height
    assert metadata.audio_bitrate == audio_bitrate
    assert metadata.has_audio is True


@pytest.mark.asyncio
async def test_video_metadata_has_no_audio():
    duration = 127.5
    width, height = 514, 512
    metadata_dict = {
        "format": {"duration": duration},
        "streams": [
            {"codec_type": "video", "height": height, "width": width},
        ]
    }

    metadata = VideoMetadata.from_json_str(json.dumps(metadata_dict))

    assert metadata.has_audio is False
