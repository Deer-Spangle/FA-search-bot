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
from telethon import TelegramClient
from telethon.errors import BadRequestError
from telethon.tl.types import TypeInputPeer

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


def _is_animated_gif(file_url: str) -> bool:
    if file_url not in Sendable.EXTENSIONS_GIF:
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
    EXTENSIONS_DOCUMENT = ["doc", "docx", "rtf", "txt", "odt", "mid", "wav", "mpeg"]
    EXTENSIONS_GIF = ["gif"]
    EXTENSIONS_VIDEO = ["webm"]  # TODO
    EXTENSIONS_AUTO_DOCUMENT = ["pdf"]
    EXTENSIONS_AUDIO = ["mp3"]
    EXTENSIONS_PHOTO = ["jpg", "jpeg", "png"]
    EXTENSIONS_ERROR = ["swf"]

    SIZE_LIMIT_IMAGE = 5 * 1000 ** 2  # Maximum 5MB image size on telegram
    SIZE_LIMIT_GIF = 8 * 1000 ** 2  # Maximum 8MB gif size on telegram
    SIZE_LIMIT_DOCUMENT = 20 * 1000 ** 2  # Maximum 20MB document size on telegram

    GIF_CACHE_DIR = "gif_cache"
    DOCKER_TIMEOUT = 5 * 60

    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    @abstractmethod
    def download_url(self) -> str:
        pass

    @property
    @abstractmethod
    def download_file_ext(self) -> str:
        pass

    @property
    @abstractmethod
    def download_file_size(self) -> int:
        pass

    @property
    @abstractmethod
    def preview_image_url(self) -> str:
        """
        For image submissions, the preview image is probably the same as the download url.
        For non-image submissions, the preview image is probably a cover image.
        """
        pass

    @property
    @abstractmethod
    def thumbnail_url(self) -> str:
        """
        A scaled down thumbnail, of the full image, or of the preview image
        """
        pass

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
                if not _is_animated_gif(file):
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
        if ext in self.EXTENSIONS_PHOTO:
            if self.download_file_size > self.SIZE_LIMIT_IMAGE:
                settings.direct_link = True
                return await send_partial(self.thumbnail_url)
            try:
                return await send_partial(self.download_url)
            except BadRequestError:
                settings.direct_link = True
                return await send_partial(self.thumbnail_url)
        # Handle gifs, which can be made pretty
        if ext in self.EXTENSIONS_GIF:
            await self._send_gif(send_partial)
            return
        # TODO: handle apng
        # TODO: handle webm
        # Everything else is a file, send with title and author
        settings.title = True
        settings.author = True
        # Handle files telegram can't handle
        if ext in self.EXTENSIONS_DOCUMENT or self.download_file_size > self.SIZE_LIMIT_DOCUMENT:
            settings.direct_link = True
            return await send_partial(self.preview_image_url)
        # Handle pdfs, which can be sent as documents
        if ext in self.EXTENSIONS_AUTO_DOCUMENT:
            return await send_partial(self.download_url, force_doc=True)
        # Handle audio
        if ext in self.EXTENSIONS_AUDIO:
            return await send_partial(self.download_url)
        # Handle known error extensions
        logger.warning("Can't send file for submission ID %s, file extension is .%s", self.id, ext)
        if ext in self.EXTENSIONS_ERROR:
            # TODO:Why not handle like document? sending preview image?
            raise CantSendFileType(f"I'm sorry, I can't neaten \".{ext}\" files.")
        raise CantSendFileType(f"I'm sorry, I don't understand that file extension ({ext}).")

    async def _send_gif(
            self,
            send_partial: Callable[[Union[str, BinaryIO, bytes]], Coroutine[None, None, None]],
    ) -> None:
        try:
            logger.info("Sending gif, submission ID %s", self.id)
            filename = self._get_gif_from_cache()
            if filename is None:
                logger.info("Gif not in cache, converting to video. Submission ID %s", self.id)
                output_path = await self._convert_gif(self.download_url)
                filename = self._save_gif_to_cache(output_path)
            await send_partial(open(filename, "rb"))
        except Exception as e:
            logger.error("Failed to convert gif to video. Submission ID: %s", self.id, exc_info=e)
            await send_partial(self.download_url)
        return

    @abstractmethod
    def caption(self, settings: CaptionSettings, prefix: Optional[str] = None):
        pass

    def _get_gif_from_cache(self) -> Optional[str]:
        # TODO: support multiple sites
        filename = f"{self.GIF_CACHE_DIR}/{self.id}.mp4"
        if os.path.exists(filename):
            logger.info("Loading gif from cache, submission ID %s", self.id)
            usage_logger.info("Pretty gif: from cache")
            return filename
        return None

    def _save_gif_to_cache(self, gif_path: str) -> str:
        # TODO: handle multiple sites
        filename = f"{self.GIF_CACHE_DIR}/{self.id}.mp4"
        os.makedirs(self.GIF_CACHE_DIR, exist_ok=True)
        os.rename(gif_path, filename)
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
        logger.info("Doing a two pass gif conversion on submission ID %s", self.id)
        two_pass_filename = random_sandbox_video_path("mp4")
        # Get video duration from ffprobe
        duration_str = await self._run_docker(
            client,
            f"-show_entries format=duration -of default=noprint_wrappers=1:nokey=1 -i /{output_path} -v error ",
            entrypoint="ffprobe"
        )
        duration = float(duration_str)
        # 2 pass run
        bitrate = self.SIZE_LIMIT_GIF / duration * 1000000 * 8
        log_file = random_sandbox_video_path("")
        await self._run_docker(
            client,
            f"-i {gif_url} {ffmpeg_options} -b:v {bitrate} -pass 1 -f mp4 -passlogfile {log_file} /dev/null -y"
        )
        await self._run_docker(
            client,
            f"-i {gif_url} {ffmpeg_options} -b:v {bitrate} -pass 2 -passlogfile {log_file} {two_pass_filename} -y"
        )
        return two_pass_filename

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
