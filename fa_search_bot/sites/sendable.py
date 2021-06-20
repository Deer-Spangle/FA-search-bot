import asyncio
import dataclasses
import datetime
import io
import logging
import os
import uuid
from abc import ABC, abstractmethod
from typing import Union, BinaryIO, Coroutine, Optional, Callable

import docker
import requests
from PIL import Image
from docker import DockerClient
from docker.models.containers import Container
from telethon import TelegramClient, Button
from telethon.errors import BadRequestError
from telethon.tl.custom import InlineBuilder
from telethon.tl.types import TypeInputPeer, InputBotInlineResultPhoto

logger = logging.getLogger(__name__)
usage_logger = logging.getLogger("usage")


@dataclasses.dataclass
class CaptionSettings:
    direct_link: bool = False
    title: bool = False
    author: bool = False


def random_sandbox_video_path(file_ext: str = "mp4"):
    os.makedirs("sandbox", exist_ok=True)
    return f"sandbox/{uuid.uuid4()}.{file_ext}"


def _is_animated(file_url: str) -> bool:
    file_ext = file_url.split(".")[-1].lower()
    if file_ext not in Sendable.EXTENSIONS_ANIMATED:
        return False
    data = requests.get(file_url).content
    with Image.open(io.BytesIO(data)) as img:
        return img.is_animated


def _convert_gif_to_png(file_url: str) -> bytes:
    data = requests.get(file_url).content
    img = Image.open(io.BytesIO(data))
    img = img.convert("RGB")
    byte_arr = io.BytesIO()
    img.save(byte_arr, format="PNG")
    return byte_arr.getvalue()


class CantSendFileType(Exception):
    pass


class Sendable(ABC):
    EXTENSIONS_GIF = ["gif"]  # These should be converted to png, if not animated
    EXTENSIONS_ANIMATED = ["gif", "png"]  # These should be converted to mp4, without sound, if they are animated
    EXTENSIONS_VIDEO = ["webm"]  # These should be converted to mp4, with sound

    EXTENSIONS_AUTO_DOCUMENT = ["pdf"]  # Telegram can embed these as documents
    EXTENSIONS_AUDIO = ["mp3"]  # Telegram can embed these as audio
    EXTENSIONS_PHOTO = ["jpg", "jpeg"]  # Telegram can embed these as images

    SIZE_LIMIT_IMAGE = 5 * 1000 ** 2  # Maximum 5MB image size on telegram
    SIZE_LIMIT_GIF = 8 * 1000 ** 2  # Maximum 8MB gif size on telegram
    SIZE_LIMIT_VIDEO = 10 * 1000 ** 2  # Maximum 10MB video autodownload size on telegram
    SIZE_LIMIT_DOCUMENT = 20 * 1000 ** 2  # Maximum 20MB document size on telegram

    CACHE_DIR = "video_cache"
    DOCKER_TIMEOUT = 5 * 60

    @property
    @abstractmethod
    def site_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def id(self) -> str:
        raise NotImplementedError

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

    async def send_message(
            self,
            client: TelegramClient,
            chat: TypeInputPeer,
            *,
            reply_to: int = None,
            prefix: str = None,
            edit: bool = False
    ) -> None:
        settings = CaptionSettings()
        ext = self.download_file_ext

        async def send_partial(file: Union[str, BinaryIO, bytes], force_doc: bool = False) -> None:
            if isinstance(file, str):
                file_ext = file.split(".")[-1].lower()
                if file_ext in self.EXTENSIONS_GIF and not _is_animated(file):
                    file = _convert_gif_to_png(file)
            if edit:
                await client.edit_message(
                    entity=chat,
                    file=file,
                    message=self.caption(settings, prefix),
                    force_document=force_doc,
                    parse_mode='html'
                )
                return
            await client.send_message(
                entity=chat,
                file=file,
                message=self.caption(settings, prefix),
                reply_to=reply_to,
                force_document=force_doc,
                parse_mode='html'  # Markdown is not safe here, because of the prefix.
            )
            return

        # Handle photos
        if ext in self.EXTENSIONS_PHOTO or (ext in self.EXTENSIONS_ANIMATED and not _is_animated(self.download_url)):
            if self.download_file_size > self.SIZE_LIMIT_IMAGE:
                settings.direct_link = True
                return await send_partial(self.thumbnail_url)
            try:
                return await send_partial(self.download_url)
            except BadRequestError:
                settings.direct_link = True
                return await send_partial(self.thumbnail_url)
        # Handle animated gifs and videos, which can be made pretty
        if ext in self.EXTENSIONS_ANIMATED + self.EXTENSIONS_VIDEO:
            return await self._send_video(send_partial)
        # Everything else is a file, send with title and author
        settings.title = True
        settings.author = True
        # Special handling, if it's small enough
        if self.download_file_size < self.SIZE_LIMIT_DOCUMENT:
            # Handle pdfs, which can be sent as documents
            if ext in self.EXTENSIONS_AUTO_DOCUMENT:
                return await send_partial(self.download_url, force_doc=True)
            # Handle audio
            if ext in self.EXTENSIONS_AUDIO:
                # TODO: can we support setting title, performer, thumb?
                return await send_partial(self.download_url)
        # Handle files telegram can't handle
        settings.direct_link = True
        return await send_partial(self.preview_image_url)

    async def _send_video(
            self,
            send_partial: Callable[[Union[str, BinaryIO, bytes]], Coroutine[None, None, None]],
    ) -> None:
        try:
            logger.info("Sending video, site ID %s, submission ID %s", self.site_id, self.id)
            filename = self._get_video_from_cache()
            if filename is None:
                logger.info("Video not in cache, converting to mp4. Submission ID %s", self.id)
                output_path = await self._convert_video(self.download_url)
                filename = self._save_video_to_cache(output_path)
            await send_partial(open(filename, "rb"))
        except Exception as e:
            logger.error(
                "Failed to convert video to mp4. Site ID: %s, Submission ID: %s",
                self.site_id,
                self.id,
                exc_info=e
            )
            await send_partial(self.download_url)
        return

    @abstractmethod
    def caption(self, settings: CaptionSettings, prefix: Optional[str] = None):
        raise NotImplementedError

    def _get_video_from_cache(self) -> Optional[str]:
        cache_dir = f"{self.CACHE_DIR}/{self.site_id}"
        filename = f"{cache_dir}/{self.id}.mp4"
        if os.path.exists(filename):
            logger.info("Loading video from cache, site ID %s, submission ID %s", self.site_id, self.id)
            usage_logger.info("Pretty video: from cache")
            return filename
        return None

    def _save_video_to_cache(self, video_path: str) -> str:
        cache_dir = f"{self.CACHE_DIR}/{self.site_id}"
        filename = f"{cache_dir}/{self.id}.mp4"
        os.makedirs(cache_dir, exist_ok=True)
        os.rename(video_path, filename)
        return filename

    async def _convert_gif(self, gif_url: str) -> str:
        usage_logger.info("Pretty gif: converting")
        ffmpeg_options = " -an -vcodec libx264 -tune animation -preset veryslow -movflags faststart -pix_fmt yuv420p " \
                         "-vf \"scale='min(1280,iw)':'min(1280,ih)':force_original_aspect_" \
                         "ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2\" -profile:v baseline -level 3.0 -vsync vfr"
        crf_option = " -crf 18"
        # first pass
        client = docker.from_env()
        output_path = random_sandbox_video_path("mp4")
        await self._run_docker(client, f"-i {gif_url} {ffmpeg_options} {crf_option} /{output_path}")
        # Check file size
        if os.path.getsize(output_path) < self.SIZE_LIMIT_GIF:
            return output_path
        # If it's too big, do a 2 pass run
        return await self._convert_two_pass(client, output_path, gif_url, ffmpeg_options)

    async def _convert_video(self, video_url: str) -> str:
        # If it's a gif, it has no audio track
        if video_url.split(".")[-1].lower() in self.EXTENSIONS_ANIMATED:
            return await self._convert_gif(video_url)
        usage_logger.info("Pretty video: converting")
        ffmpeg_options = "-qscale 0"
        # first pass
        client = docker.from_env()
        output_path = random_sandbox_video_path("mp4")
        await self._run_docker(client, f"-i {video_url} {ffmpeg_options} /{output_path}")
        # If it doesn't have an audio track, handle it as a gif
        if not await self._video_has_audio_track(client, output_path):
            return await self._convert_gif(video_url)
        # Check file size
        if os.path.getsize(output_path) < self.SIZE_LIMIT_VIDEO:
            return output_path
        # If it's too big, do a 2 pass run
        return await self._convert_two_pass(client, output_path, video_url, ffmpeg_options)

    async def _convert_two_pass(
            self,
            client: DockerClient,
            sandbox_path: str,
            video_url: str,
            ffmpeg_options: str
    ) -> str:
        logger.info("Doing a two pass video conversion on site ID %s, submission ID %s", self.site_id, self.id)
        two_pass_filename = random_sandbox_video_path("mp4")
        # Get video duration from ffprobe
        duration = await self._video_duration(client, sandbox_path)
        # 2 pass run
        bitrate = (self.SIZE_LIMIT_VIDEO / duration) * 8
        log_file = random_sandbox_video_path("log")
        await self._run_docker(
            client,
            f"-i {video_url} {ffmpeg_options} -b:v {bitrate} -pass 1 -f mp4 -passlogfile /{log_file} /dev/null -y"
        )
        await self._run_docker(
            client,
            f"-i {video_url} {ffmpeg_options} -b:v {bitrate} -pass 2 -passlogfile /{log_file} /{two_pass_filename} -y"
        )
        return two_pass_filename

    async def _video_has_audio_track(self, client: DockerClient, sandbox_path: str) -> bool:
        audio_track_str = await self._run_docker(
            client,
            f"-show_streams -select_streams a -loglevel error /{sandbox_path} -v error ",
            entrypoint="ffprobe"
        )
        return bool(len(audio_track_str))

    async def _video_duration(self, client: DockerClient, sandbox_path: str) -> float:
        duration_str = await self._run_docker(
            client,
            f"-show_entries format=duration -of default=noprint_wrappers=1:nokey=1 -i /{sandbox_path} -v error ",
            entrypoint="ffprobe"
        )
        return float(duration_str)

    async def _run_docker(self, client: DockerClient, args: str, entrypoint: Optional[str] = None) -> str:
        sandbox_dir = os.getcwd() + "/sandbox"
        logger.debug("Running docker container with args %s and entrypoint %s", args, entrypoint)
        container: Container = client.containers.run(
            "jrottenberg/ffmpeg:alpine",
            args,
            entrypoint=entrypoint,
            volumes={sandbox_dir: {"bind": "/sandbox", "mode": "rw"}},
            working_dir="/sandbox",
            detach=True
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

    def to_inline_query_result(self, builder: InlineBuilder) -> Coroutine[None, None, InputBotInlineResultPhoto]:
        return builder.photo(
            file=self.thumbnail_url,
            id=f"{self.site_id}:{self.id}",
            text=self.link,
            # Button is required such that the bot can get a callback with the message id, and edit it later.
            buttons=[Button.inline("⏳ Optimising", f"neaten_me:{self.site_id}:{self.id}")]
        )
