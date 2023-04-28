from __future__ import annotations

import asyncio
import dataclasses
import datetime
import enum
import io
import logging
import os
import uuid
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Callable, TypeVar, Generator

import docker
import requests
from PIL import Image
from prometheus_client import Counter, Summary
from prometheus_client.metrics import Histogram
from telethon import Button

from fa_search_bot.sites.sent_submission import SentSubmission, sent_from_cache

if TYPE_CHECKING:
    from typing import Any, Awaitable, BinaryIO, Optional, Union

    from docker import DockerClient
    from docker.models.containers import Container
    from telethon import TelegramClient
    from telethon.tl.custom import InlineBuilder
    from telethon.tl.types import InputBotInlineResultPhoto, TypeInputPeer

    from fa_search_bot.sites.handler_group import HandlerGroup
    from fa_search_bot.sites.submission_id import SubmissionID

logger = logging.getLogger(__name__)

sendable_sent = Counter(
    "fasearchbot_sendable_sent_message_total",
    "Number of submissions sent or edited, labelled by site",
    labelnames=["site_code"],
)
sendable_gif_to_png = Counter(
    "fasearchbot_sendable_convert_gif_to_png_total",
    "Number of images which were converted from static gif to png",
    labelnames=["site_code"],
)
sendable_edit = Counter(
    "fasearchbot_sendable_edit_total",
    "Number of submissions which were sent as an edit",
    labelnames=["site_code"],
)
sendable_failure = Counter(
    "fasearchbot_sendable_exception_total",
    "Number of sendable attempts which raised an exception",
    labelnames=["site_code"],
)
sendable_image = Counter(
    "fasearchbot_sendable_image_total",
    "Number of static images which were sent",
    labelnames=["site_code"],
)
sendable_animated = Counter(
    "fasearchbot_sendable_animated_total",
    "Number of animated images and videos which were sent",
    labelnames=["site_code"],
)
sendable_animated_cached = Counter(
    "fasearchbot_sendable_animated_cached_total",
    "Number of animated images and videos which were sent from file cache",
    labelnames=["site_code"],
)
sendable_auto_doc = Counter(
    "fasearchbot_sendable_auto_document_total",
    "Number of documents sent which telegram can automatically handle",
    labelnames=["site_code"],
)
sendable_audio = Counter(
    "fasearchbot_sendable_audio_total",
    "Number of audio files which were sent",
    labelnames=["site_code"],
)
sendable_other = Counter(
    "fasearchbot_sendable_other_files_total",
    "Number of files sent which had no special handling",
    labelnames=["site_code"],
)

convert_video_total = Counter(
    "fasearchbot_convert_video_total",
    "Number of animated images or videos which we tried to process",
    labelnames=["site_code"],
)
convert_video_failures = Counter(
    "fasearchbot_convert_video_exception_total",
    "Number of video conversions which raised an exception",
    labelnames=["site_code"],
)
convert_video_animated = Counter(
    "fasearchbot_convert_video_animated_total",
    "Number of animated images which we tried to convert to a video",
    labelnames=["site_code"],
)
convert_video_no_audio = Counter(
    "fasearchbot_convert_video_no_audio_total",
    "Number of videos without audio which we tried to convert",
    labelnames=["site_code"],
)
convert_video_no_audio_gif = Counter(
    "fasearchbot_convert_video_no_audio_gif_total",
    "Number of videos without audio which we tried to convert to a telegram gif",
    labelnames=["site_code"],
)
convert_video_to_video = Counter(
    "fasearchbot_convert_video_to_video_total",
    "Number of videos which we tried to convert into a video with audio",
    labelnames=["site_code"],
)
convert_video_only_one_attempt = Counter(
    "fasearchbot_convert_video_only_one_attempt_total",
    "Number of videos which we converted with a one-pass conversion attempt",
    labelnames=["site_code"],
)
convert_video_two_pass = Counter(
    "fasearchbot_convert_video_two_pass_total",
    "Number of videos which required a two-pass conversion to fit within telegram limits",
    labelnames=["site_code"],
)

convert_gif_total = Counter(
    "fasearchbot_convert_gif_total",
    "Number of animated images or short silent videos we tried to convert into telegram gifs",
    labelnames=["site_code"],
)
convert_gif_failures = Counter(
    "fasearchbot_convert_gif_exception_total",
    "Number of telegram gif conversions which raised an exception",
    labelnames=["site_code"],
)
convert_gif_only_one_attempt = Counter(
    "fasearchbot_convert_gif_only_one_attempt_total",
    "Number of telegram gifs which required only one-pass conversion",
    labelnames=["site_code"],
)
convert_gif_two_pass = Counter(
    "fasearchbot_convert_gif_two_pass_total",
    "Number of telegram gifs which required two-pass conversion to fit within telegram limits",
    labelnames=["site_code"],
)

video_length = Histogram(
    "fasearchbot_video_length_seconds",
    "Length of the videos processed by the bot, in seconds",
    buckets=[1, 2, 5, 10, 30, 60, 120, 300, 600, 1200, float("inf")],
    labelnames=["site_code"],
)

docker_run_time = Histogram(
    "fasearchbot_docker_runtime_seconds",
    "Time the docker image took to run and return, in seconds",
    buckets=[0.5, 1, 2, 5, 10, 30, 60, 120, 300, 600, float("inf")],
    labelnames=["site_code", "entrypoint"],
)
docker_failures = Counter(
    "fasearchbot_docker_failure_total",
    "Number of times an exception was raised while running a docker image",
    labelnames=["site_code", "entrypoint"],
)

inline_results = Counter(
    "fasearchbot_sendable_inline_result_total",
    "Total number of inline results sent",
    labelnames=["site_code"],
)

time_taken = Summary(
    "fasearchbot_sendable_time_taken",
    "Amount of time taken (in seconds) doing various parts of sending a message",
    labelnames=["task"],
)
time_taken_downloading_image = time_taken.labels(task="downloading image")
time_taken_converting_static_gif = time_taken.labels(task="converting static gif to png")
time_taken_editing_message = time_taken.labels(task="editing message")
time_taken_sending_message = time_taken.labels(task="sending message")
time_taken_converting_video = time_taken.labels(task="converting video")
time_taken_fetching_filesize = time_taken.labels(task="fetching filesize")

SANDBOX_DIR = "sandbox"


@dataclasses.dataclass
class CaptionSettings:
    direct_link: bool = False
    title: bool = False
    author: bool = False


def initialise_metrics_labels(handlers: HandlerGroup) -> None:
    for site_code in handlers.site_codes():
        for metric in [
            sendable_sent, sendable_gif_to_png, sendable_edit, sendable_failure, sendable_image, sendable_animated,
            sendable_auto_doc, sendable_audio, sendable_other, sendable_animated_cached, convert_video_total,
            convert_video_failures, convert_video_animated, convert_video_no_audio, convert_video_no_audio_gif,
            convert_video_to_video, convert_video_only_one_attempt, convert_video_two_pass, convert_gif_total,
            convert_gif_failures, convert_gif_only_one_attempt, convert_gif_two_pass, video_length, sent_from_cache,
        ]:
            metric.labels(site_code=site_code)
        for entrypoint in DockerEntrypoint:
            docker_run_time.labels(site_code=site_code, entrypoint=entrypoint.value)
            docker_failures.labels(site_code=site_code, entrypoint=entrypoint.value)
        inline_results.labels(site_code=site_code)


def random_sandbox_video_path(file_ext: str = "mp4") -> str:
    os.makedirs(SANDBOX_DIR, exist_ok=True)
    return f"{SANDBOX_DIR}/{uuid.uuid4()}.{file_ext}"


@contextmanager
def temp_sandbox_file(file_ext: str = "mp4") -> Generator[str, None, None]:
    temp_path = random_sandbox_video_path(file_ext)
    try:
        yield temp_path
    finally:
        try:
            os.remove(temp_path)
        except FileNotFoundError:
            pass


def _is_animated(file_url: str) -> bool:
    file_ext = file_url.split(".")[-1].lower()
    if file_ext not in Sendable.EXTENSIONS_ANIMATED:
        return False
    data = requests.get(file_url).content
    with Image.open(io.BytesIO(data)) as img:
        # is_animated attribute might not exist, if file is a jpg named ".png"
        return getattr(img, "is_animated", False)


def _convert_gif_to_png(file_url: str) -> bytes:
    data = requests.get(file_url).content
    img = Image.open(io.BytesIO(data))
    img = img.convert("RGB")
    byte_arr = io.BytesIO()
    img.save(byte_arr, format="PNG")
    return byte_arr.getvalue()


WrapReturn = TypeVar("WrapReturn", covariant=True)
WrapFunc = Callable[..., WrapReturn]


def _count_exceptions_with_labels(counter: Counter) -> Callable[[WrapFunc], WrapFunc]:
    def _count_exceptions(f: WrapFunc) -> WrapFunc:
        async def wrapper(s: "Sendable", *args: Any, **kwargs: Any) -> WrapReturn:
            self = s
            with counter.labels(site_code=self.site_id).count_exceptions():
                return await f(self, *args, **kwargs)

        return wrapper

    return _count_exceptions


class DockerEntrypoint(enum.Enum):
    FFMPEG = "ffmpeg"
    FFPROBE = "ffprobe"
    OTHER = "other"

    @classmethod
    def from_string(cls, entrypoint_string: Optional[str]) -> "DockerEntrypoint":
        if entrypoint_string is None:
            return cls.FFMPEG
        if entrypoint_string == "ffprobe":
            return cls.FFPROBE
        return cls.OTHER


class CantSendFileType(Exception):
    pass


def _format_input_path(input_path: str) -> str:
    if input_path.lower().startswith("http"):
        return f"-i {input_path}"
    return f"/{input_path}"


class InlineSendable(ABC):

    @property
    def site_id(self) -> str:
        return self.submission_id.site_code

    @property
    def id(self) -> str:
        return self.submission_id.submission_id

    @property
    @abstractmethod
    def submission_id(self) -> SubmissionID:
        raise NotImplementedError

    @property
    @abstractmethod
    def thumbnail_url(self) -> str:
        """
        A scaled down thumbnail, of the full image, or of the preview image
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def link(self) -> str:
        raise NotImplementedError

    def to_inline_query_result(self, builder: InlineBuilder) -> Awaitable[InputBotInlineResultPhoto]:
        inline_results.labels(site_code=self.site_id).inc()
        return builder.photo(
            file=self.thumbnail_url,
            id=f"{self.site_id}:{self.id}",
            text=self.link,
            # Button is required such that the bot can get a callback with the message id, and edit it later.
            buttons=[Button.inline("⏳ Optimising", f"neaten_me:{self.submission_id.to_inline_code()}")],
        )


class Sendable(InlineSendable):
    EXTENSIONS_GIF = ["gif"]  # These should be converted to png, if not animated
    EXTENSIONS_ANIMATED = [
        "gif",
        "png",
    ]  # These should be converted to mp4, without sound, if they are animated
    EXTENSIONS_VIDEO = ["webm"]  # These should be converted to mp4, with sound

    EXTENSIONS_AUTO_DOCUMENT = ["pdf"]  # Telegram can embed these as documents
    EXTENSIONS_AUDIO = ["mp3"]  # Telegram can embed these as audio
    EXTENSIONS_PHOTO = ["jpg", "jpeg"]  # Telegram can embed these as images
    # Maybe use these for labels

    SIZE_LIMIT_IMAGE = 5 * 1000**2  # Maximum 5MB image size on telegram
    SIZE_LIMIT_GIF = 8 * 1000**2  # Maximum 8MB gif size on telegram
    SIZE_LIMIT_VIDEO = 10 * 1000**2  # Maximum 10MB video autodownload size on telegram
    SIZE_LIMIT_DOCUMENT = 20 * 1000**2  # Maximum 20MB document size on telegram
    LENGTH_LIMIT_GIF = 40  # Maximum 40 seconds for gifs, otherwise video, for ease

    DOCKER_TIMEOUT = 5 * 60

    @property
    @abstractmethod
    def download_url(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def download_file_ext(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def download_file_size(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def preview_image_url(self) -> str:
        """
        For image submissions, the preview image is probably the same as the download url.
        For non-image submissions, the preview image is probably a cover image.
        """
        raise NotImplementedError

    @_count_exceptions_with_labels(sendable_failure)
    async def send_message(
        self,
        client: TelegramClient,
        chat: TypeInputPeer,
        *,
        reply_to: int = None,
        prefix: str = None,
        edit: bool = False,
    ) -> SentSubmission:
        sendable_sent.labels(site_code=self.site_id).inc()
        settings = CaptionSettings()
        ext = self.download_file_ext

        async def send_partial(file: Union[str, BinaryIO, bytes], force_doc: bool = False) -> SentSubmission:
            if isinstance(file, str):
                file_ext = file.split(".")[-1].lower()
                if file_ext in self.EXTENSIONS_GIF and not _is_animated(file):
                    sendable_gif_to_png.labels(site_code=self.site_id).inc()
                    with time_taken_converting_static_gif.time():
                        file = _convert_gif_to_png(file)
            if edit:
                sendable_edit.labels(site_code=self.site_id).inc()
                with time_taken_editing_message.time():
                    msg = await client.edit_message(
                        entity=chat,
                        file=file,
                        message=self.caption(settings, prefix),
                        force_document=force_doc,
                        parse_mode="html",
                    )
            else:
                with time_taken_sending_message.time():
                    msg = await client.send_message(
                        entity=chat,
                        file=file,
                        message=self.caption(settings, prefix),
                        reply_to=reply_to,
                        force_document=force_doc,
                        parse_mode="html",  # Markdown is not safe here, because of the prefix.
                    )
            return SentSubmission.from_resp(self.submission_id, msg, self.download_url, self.caption(settings))

        # Handle photos
        if ext in self.EXTENSIONS_PHOTO or (ext in self.EXTENSIONS_ANIMATED and not _is_animated(self.download_url)):
            sendable_image.labels(site_code=self.site_id).inc()
            with temp_sandbox_file(ext) as dl_path:
                with time_taken_downloading_image.time():
                    resp = requests.get(self.download_url, stream=True)
                    dl_filesize = 0
                    with open(dl_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                            dl_filesize += len(chunk)
                # TODO: Check image resolution
                if dl_filesize > self.SIZE_LIMIT_IMAGE:
                    settings.direct_link = True
                return await send_partial(dl_path)
        # Handle animated gifs and videos, which can be made pretty
        if ext in self.EXTENSIONS_ANIMATED + self.EXTENSIONS_VIDEO:
            sendable_animated.labels(site_code=self.site_id).inc()
            try:
                logger.info("Sending video, submission ID %s, converting to mp4", self.submission_id)
                with time_taken_converting_video.time():
                    output_path: str = await self._convert_video(self.download_url)
                return await send_partial(output_path)
            except Exception as e:
                logger.error("Failed to convert video to mp4. Submission ID: %s", self.submission_id, exc_info=e)
                return await send_partial(self.download_url)
        # Everything else is a file, send with title and author
        settings.title = True
        settings.author = True
        # Special handling, if it's small enough
        with time_taken_fetching_filesize.time():
            dl_filesize = self.download_file_size
        if dl_filesize < self.SIZE_LIMIT_DOCUMENT:
            # Handle pdfs, which can be sent as documents
            if ext in self.EXTENSIONS_AUTO_DOCUMENT:
                sendable_auto_doc.labels(site_code=self.site_id).inc()
                return await send_partial(self.download_url, force_doc=True)
            # Handle audio
            if ext in self.EXTENSIONS_AUDIO:
                sendable_audio.labels(site_code=self.site_id).inc()
                # TODO: can we support setting title, performer, thumb?
                return await send_partial(self.download_url)
        # Handle files telegram can't handle
        sendable_other.labels(site_code=self.site_id).inc()
        settings.direct_link = True
        return await send_partial(self.preview_image_url)

    async def _send_video(
        self,
        send_partial: Callable[[Union[str, BinaryIO, bytes]], Awaitable[SentSubmission]],
    ) -> SentSubmission:
        try:
            logger.info("Sending video, site ID %s, submission ID %s, converting to mp4", self.site_id, self.id)
            output_path: str = await self._convert_video(self.download_url)
            return await send_partial(output_path)
        except Exception as e:
            logger.error(
                "Failed to convert video to mp4. Site ID: %s, Submission ID: %s",
                self.site_id,
                self.id,
                exc_info=e,
            )
            return await send_partial(self.download_url)

    @abstractmethod
    def caption(self, settings: CaptionSettings, prefix: Optional[str] = None) -> str:
        raise NotImplementedError  # TODO: Pull caption builder out, I guess? Three implementations of caption data?

    @_count_exceptions_with_labels(convert_gif_failures)
    async def _convert_gif(self, gif_url: str) -> str:
        convert_gif_total.labels(site_code=self.site_id).inc()
        ffmpeg_options = (
            " -an -vcodec libx264 -tune animation -preset veryslow -movflags faststart -pix_fmt yuv420p "
            "-vf \"scale='min(1280,iw)':'min(1280,ih)':force_original_aspect_"
            'ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2" -profile:v baseline -level 3.0 -vsync vfr'
        )
        crf_option = " -crf 18"
        # first pass
        client = docker.from_env()
        output_path = random_sandbox_video_path("mp4")
        await self._run_docker(client, f"-i {gif_url} {ffmpeg_options} {crf_option} /{output_path}")
        # Check file size
        if os.path.getsize(output_path) < self.SIZE_LIMIT_GIF:
            convert_gif_only_one_attempt.labels(site_code=self.site_id).inc()
            return output_path
        # If it's too big, do a 2 pass run
        convert_gif_two_pass.labels(site_code=self.site_id).inc()
        return await self._convert_two_pass(client, output_path, gif_url, ffmpeg_options)

    @_count_exceptions_with_labels(convert_video_failures)
    async def _convert_video(self, video_url: str) -> str:
        convert_video_total.labels(site_code=self.site_id).inc()
        # If it's a gif, it has no audio track
        if video_url.split(".")[-1].lower() in self.EXTENSIONS_ANIMATED:
            convert_video_animated.labels(site_code=self.site_id).inc()
            return await self._convert_gif(video_url)
        client = docker.from_env()
        ffmpeg_options = "-qscale 0"
        ffmpeg_prefix = ""
        # Check if it has audio
        has_audio = await self._video_has_audio_track(client, video_url)
        if not has_audio:
            convert_video_no_audio.labels(site_code=self.site_id).inc()
            ffmpeg_options = "-qscale:v 0 -acodec aac -map 0:0 -map 1:0 -shortest"
            ffmpeg_prefix = "-f lavfi -i aevalsrc=0"
            if await self._video_duration(client, video_url) < self.LENGTH_LIMIT_GIF:
                convert_video_no_audio_gif.labels(site_code=self.site_id).inc()
                return await self._convert_gif(video_url)
        # first pass
        convert_video_to_video.labels(site_code=self.site_id).inc()
        output_path = random_sandbox_video_path("mp4")
        await self._run_docker(client, f"{ffmpeg_prefix} -i {video_url} {ffmpeg_options} /{output_path}")
        # Check file size
        if os.path.getsize(output_path) < self.SIZE_LIMIT_VIDEO:
            convert_video_only_one_attempt.labels(site_code=self.site_id).inc()
            return output_path
        # If it's too big, do a 2 pass run
        convert_video_two_pass.labels(site_code=self.site_id).inc()
        return await self._convert_two_pass(client, output_path, video_url, ffmpeg_options, ffmpeg_prefix)

    async def _convert_two_pass(
        self,
        client: DockerClient,
        sandbox_path: str,
        video_url: str,
        ffmpeg_options: str,
        ffmpeg_prefix: str = "",
    ) -> str:
        logger.info(
            "Doing a two pass video conversion on site ID %s, submission ID %s",
            self.site_id,
            self.id,
        )
        two_pass_filename = random_sandbox_video_path("mp4")
        # Get video duration from ffprobe
        duration = await self._video_duration(client, sandbox_path)
        # 2 pass run
        bitrate = (self.SIZE_LIMIT_VIDEO / duration) * 8
        # If it has an audio stream, subtract audio bitrate from total bitrate to get video bitrate
        if await self._video_has_audio_track(client, sandbox_path):
            audio_bitrate = await self._video_audio_bitrate(client, sandbox_path)
            bitrate = bitrate - audio_bitrate
            if bitrate < 0:
                logger.error(
                    "Desired bitrate for submission (site id %s sub id %s) is higher than the audio bitrate alone.",
                    self.site_id,
                    self.id,
                )
                raise ValueError("Bitrate cannot be negative")
        with temp_sandbox_file("log") as log_file:
            full_ffmpeg_options = f"{ffmpeg_prefix} -i {video_url} {ffmpeg_options} -b:v {bitrate}"
            await self._run_docker(
                client,
                f"{full_ffmpeg_options} -pass 1 -f mp4 -passlogfile /{log_file} /dev/null -y",
            )
            await self._run_docker(
                client,
                f"{full_ffmpeg_options} -pass 2 -passlogfile /{log_file} /{two_pass_filename} -y",
            )
        return two_pass_filename

    async def _video_has_audio_track(self, client: DockerClient, input_path: str) -> bool:
        input_path = _format_input_path(input_path)
        audio_track_str = await self._run_docker(
            client,
            f"-show_streams -select_streams a -loglevel error {input_path} -v error ",
            entrypoint="ffprobe",
        )
        return bool(len(audio_track_str))

    async def _video_audio_bitrate(self, client: DockerClient, input_path: str) -> float:
        input_path = _format_input_path(input_path)
        audio_bitrate_str = await self._run_docker(
            client,
            f"-v error -select_streams a -show_entries stream=bit_rate -of default=noprint_wrappers=1:nokey=1 "
            f"{input_path}",
            entrypoint="ffprobe",
        )
        return float(audio_bitrate_str)

    async def _video_duration(self, client: DockerClient, input_path: str) -> float:
        input_path = _format_input_path(input_path)
        duration_str = await self._run_docker(
            client,
            f"-show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {input_path} -v error ",
            entrypoint="ffprobe",
        )
        duration = float(duration_str)
        video_length.labels(site_code=self.site_id).observe(duration)
        return duration

    async def _run_docker(self, client: DockerClient, args: str, entrypoint: Optional[str] = None) -> str:
        labels = {
            "site_code": self.site_id,
            "entrypoint": DockerEntrypoint.from_string(entrypoint).value,
        }
        with docker_run_time.labels(**labels).time():
            with docker_failures.labels(**labels).count_exceptions():
                sandbox_dir = os.getcwd() + "/" + SANDBOX_DIR
                logger.debug(
                    "Running docker container with args %s and entrypoint %s",
                    args,
                    entrypoint,
                )
                container: Container = client.containers.run(
                    "jrottenberg/ffmpeg:alpine",
                    args,
                    entrypoint=entrypoint,
                    volumes={sandbox_dir: {"bind": "/sandbox", "mode": "rw"}},
                    working_dir="/sandbox",
                    detach=True,
                )
                start_time = datetime.datetime.now()
                while (datetime.datetime.now() - start_time).total_seconds() < self.DOCKER_TIMEOUT:
                    container.reload()
                    if container.status == "exited":
                        output = container.logs()
                        container.remove(force=True)
                        return output
                    await asyncio.sleep(2)
                # Kill container
                logger.warning("Docker timed out, killing container.")
                container.kill()
                container.remove(force=True)
                raise TimeoutError("Docker container timed out")
