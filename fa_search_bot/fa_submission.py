import datetime
import logging
import os
import re
import time
import uuid
from abc import ABC
from enum import Enum
from typing import Dict, Union, List, Optional

import dateutil.parser
import docker
import requests
import telegram
from docker import DockerClient
from docker.models.containers import Container
from telegram import InlineQueryResultPhoto

logger = logging.getLogger(__name__)
usage_logger = logging.getLogger("usage")


class CantSendFileType(Exception):
    pass


class Rating(Enum):
    GENERAL = 1
    MATURE = 2
    ADULT = 3


def random_sandbox_video_path(file_ext: str = "mp4"):
    os.makedirs("sandbox", exist_ok=True)
    return f"sandbox/{uuid.uuid4()}.{file_ext}"


class FAUser(ABC):

    def __init__(self, name: str, profile_name: str):
        self.name = name
        self.profile_name = profile_name
        self.link = f"https://furaffinity.net/user/{profile_name}/"

    @staticmethod
    def from_short_dict(short_dict: Dict[str, str]) -> Union['FAUserShort']:
        return FAUser.from_submission_dict(short_dict)

    @staticmethod
    def from_submission_dict(short_dict: Dict[str, str]) -> Union['FAUserShort']:
        name = short_dict['name']
        profile_name = short_dict['profile_name']
        new_user = FAUserShort(name, profile_name)
        return new_user


class FAUserShort(FAUser):

    def __init__(self, name: str, profile_name: str):
        super().__init__(name, profile_name)


class FASubmission(ABC):
    EXTENSIONS_DOCUMENT = ["doc", "docx", "rtf", "txt", "odt", "mid", "wav", "mpeg"]
    EXTENSIONS_GIF = ["gif"]
    EXTENSIONS_AUTO_DOCUMENT = ["pdf"]
    EXTENSIONS_AUDIO = ["mp3"]
    EXTENSIONS_PHOTO = ["jpg", "jpeg", "png"]
    EXTENSIONS_ERROR = ["swf"]

    SIZE_LIMIT_IMAGE = 5 * 1000 ** 2  # Maximum 5MB image size on telegram
    SIZE_LIMIT_GIF = 8 * 1000 ** 2  # Maximum 8MB gif size on telegram
    SIZE_LIMIT_DOCUMENT = 20 * 1000 ** 2  # Maximum 20MB document size on telegram

    GIF_CACHE_DIR = "gif_cache"
    DOCKER_TIMEOUT = 5 * 60

    def __init__(self, submission_id: str) -> None:
        self.submission_id = submission_id
        self.link = f"https://furaffinity.net/view/{submission_id}/"

    @staticmethod
    def from_short_dict(short_dict: Dict[str, str]) -> Union['FASubmissionShortFav', 'FASubmissionShort']:
        submission_id = short_dict['id']
        thumbnail_url = FASubmission.make_thumbnail_bigger(short_dict['thumbnail'])
        title = short_dict['title']
        author = FAUser.from_short_dict(short_dict)
        if "fav_id" in short_dict:
            new_submission = FASubmissionShortFav(submission_id, thumbnail_url, title, author, short_dict['fav_id'])
        else:
            new_submission = FASubmissionShort(submission_id, thumbnail_url, title, author)
        return new_submission

    @staticmethod
    def from_full_dict(full_dict: Dict[str, Union[str, List[str]]]) -> 'FASubmissionFull':
        submission_id = FASubmission.id_from_link(full_dict['link'])
        thumbnail_url = FASubmission.make_thumbnail_bigger(full_dict['thumbnail'])
        download_url = full_dict['download']
        full_image_url = full_dict['full']
        title = full_dict['title']
        description = full_dict['description_body']
        author = FAUser.from_submission_dict(full_dict)
        keywords: List[str] = full_dict['keywords']
        rating = {
            "Adult": Rating.ADULT,
            "Mature": Rating.MATURE,
            "General": Rating.GENERAL
        }[full_dict["rating"]]
        new_submission = FASubmissionFull(
            submission_id, thumbnail_url, download_url, full_image_url, title, author, description, keywords, rating
        )
        return new_submission

    @staticmethod
    def make_thumbnail_bigger(thumbnail_url: str) -> str:
        return re.sub('@[0-9]+-', '@1600-', thumbnail_url)

    @staticmethod
    def make_thumbnail_smaller(thumbnail_url: str) -> str:
        return re.sub('@[0-9]+-', '@300-', thumbnail_url)

    @staticmethod
    def id_from_link(link: str) -> str:
        return re.search('view/([0-9]+)', link).group(1)

    @staticmethod
    def _get_file_size(url: str) -> int:
        resp = requests.head(url)
        return int(resp.headers['content-length'])


class FASubmissionShort(FASubmission):

    def __init__(self, submission_id: str, thumbnail_url: str, title: str, author: FAUser) -> None:
        super().__init__(submission_id)
        self.thumbnail_url = thumbnail_url
        self.title = title
        self.author = author

    def to_inline_query_result(self) -> InlineQueryResultPhoto:
        return InlineQueryResultPhoto(
            id=self.submission_id,
            photo_url=self.thumbnail_url,
            thumb_url=FASubmission.make_thumbnail_smaller(self.thumbnail_url),
            caption=self.link
        )


class FASubmissionShortFav(FASubmissionShort):

    def __init__(self, submission_id: str, thumbnail_url: str, title: str, author: FAUser, fav_id: str) -> None:
        super().__init__(submission_id, thumbnail_url, title, author)
        self.fav_id = fav_id


class FASubmissionFull(FASubmissionShort):

    def __init__(
            self,
            submission_id: str,
            thumbnail_url: str,
            download_url: str,
            full_image_url: str,
            title: str,
            author: FAUser,
            description: str,
            keywords: List[str],
            rating: Rating
    ) -> None:
        super().__init__(submission_id, thumbnail_url, title, author)
        self.download_url = download_url
        self.full_image_url = full_image_url
        self.description = description
        self.keywords = keywords
        self.rating = rating
        self._download_file_size = None

    @property
    def download_file_size(self) -> int:
        if self._download_file_size is None:
            self._download_file_size = FASubmission._get_file_size(self.download_url)
        return self._download_file_size

    def send_message(self, bot, chat_id: int, reply_to: int = None, prefix: str = None) -> None:
        if prefix is None:
            prefix = ""
        else:
            prefix += "\n"
        ext = self.download_url.split(".")[-1].lower()
        # Handle photos
        if ext in FASubmission.EXTENSIONS_PHOTO:
            if self.download_file_size > self.SIZE_LIMIT_IMAGE:
                bot.send_photo(
                    chat_id=chat_id,
                    photo=self.thumbnail_url,
                    caption=f"{prefix}{self.link}\n<a href=\"{self.download_url}\">Direct download</a>",
                    reply_to_message_id=reply_to,
                    parse_mode=telegram.ParseMode.HTML  # Markdown is not safe here, because of the prefix.
                )
                return
            bot.send_photo_with_backup(
                chat_id,
                {
                    "photo": self.download_url,
                    "caption": f"{prefix}{self.link}",
                    "reply_to_message_id": reply_to
                },
                {
                    "photo": self.thumbnail_url,
                    "caption": f"{prefix}{self.link}\n<a href=\"{self.download_url}\">Direct download</a>",
                    "reply_to_message_id": reply_to,
                    "parse_mode": telegram.ParseMode.HTML  # Markdown is not safe here, because of the prefix.
                }
            )
            return
        # Handle files telegram can't handle
        if ext in FASubmission.EXTENSIONS_DOCUMENT or self.download_file_size > self.SIZE_LIMIT_DOCUMENT:
            bot.send_photo(
                chat_id=chat_id,
                photo=self.full_image_url,
                caption=f"{prefix}{self.link}\n<a href=\"{self.download_url}\">Direct download</a>",
                reply_to_message_id=reply_to,
                parse_mode=telegram.ParseMode.HTML  # Markdown is not safe here, because of the prefix.
            )
            return
        # Handle gifs, which can be made pretty
        if ext in FASubmission.EXTENSIONS_GIF:
            self._send_gif(bot, chat_id, reply_to=reply_to, prefix=prefix)
            return
        # Handle pdfs, which can be sent as documents
        if ext in FASubmission.EXTENSIONS_AUTO_DOCUMENT:
            bot.send_document(
                chat_id=chat_id,
                document=self.download_url,
                caption=f"{prefix}{self.link}",
                reply_to_message_id=reply_to
            )
            return
        # Handle audio
        if ext in FASubmission.EXTENSIONS_AUDIO:
            bot.send_audio(
                chat_id=chat_id,
                audio=self.download_url,
                caption=f"{prefix}{self.link}",
                reply_to_message_id=reply_to
            )
            return
        # Handle known error extensions
        logger.warning("Can't send file for submission ID %s, file extension is .%s", self.submission_id, ext)
        if ext in FASubmission.EXTENSIONS_ERROR:
            raise CantSendFileType(f"I'm sorry, I can't neaten \".{ext}\" files.")
        raise CantSendFileType(f"I'm sorry, I don't understand that file extension ({ext}).")

    def _send_gif(self, bot, chat_id: int, reply_to: int = None, prefix: str = None) -> None:
        try:
            logger.info("Sending gif, submission ID %s", self.submission_id)
            filename = self._get_gif_from_cache()
            if filename is None:
                logger.info("Gif not in cache, converting to video. Submission ID %s", self.submission_id)
                output_path = self._convert_gif(self.download_url)
                filename = self._save_gif_to_cache(output_path)
            bot.send_document(
                chat_id=chat_id,
                document=open(filename, "rb"),
                caption=f"{prefix}{self.link}",
                reply_to_message_id=reply_to
            )
        except Exception as e:
            logger.error("Failed to convert gif to video. Submission ID: %s", self.submission_id, exc_info=e)
            bot.send_document(
                chat_id=chat_id,
                document=self.download_url,
                caption=f"{prefix}{self.link}",
                reply_to_message_id=reply_to
            )
        return

    def _get_gif_from_cache(self) -> Optional[str]:
        filename = f"{self.GIF_CACHE_DIR}/{self.submission_id}.mp4"
        if os.path.exists(filename):
            logger.info("Loading gif from cache, submission ID %s", self.submission_id)
            usage_logger.info("Pretty gif: from cache")
            return filename
        return None

    def _save_gif_to_cache(self, gif_path: str) -> str:
        filename = f"{self.GIF_CACHE_DIR}/{self.submission_id}.mp4"
        os.makedirs(self.GIF_CACHE_DIR, exist_ok=True)
        os.rename(gif_path, filename)
        return filename

    def _convert_gif(self, gif_url: str) -> str:
        usage_logger.info("Pretty gif: converting")
        ffmpeg_options = " -an -vcodec libx264 -tune animation -preset veryslow -movflags faststart -pix_fmt yuv420p " \
                         "-vf \"scale='min(1280,iw)':'min(1280,ih)':force_original_aspect_" \
                         "ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2\" -profile:v baseline -level 3.0 -vsync vfr"
        crf_option = " -crf 18"
        # first pass
        client = docker.from_env()
        output_path = random_sandbox_video_path("mp4")
        self._run_docker(client, f"-i {gif_url} {ffmpeg_options} {crf_option} /{output_path}")
        # Check file size
        if os.path.getsize(output_path) < self.SIZE_LIMIT_GIF:
            return output_path
        # If it's too big, do a 2 pass run
        logger.info("Doing a two pass gif conversion on submission ID %s", self.submission_id)
        two_pass_filename = random_sandbox_video_path("mp4")
        # Get video duration from ffprobe
        duration_str = self._run_docker(
            client,
            f"-show_entries format=duration -of default=noprint_wrappers=1:nokey=1 -i /{output_path} -v error ",
            entrypoint="ffprobe"
        )
        duration = float(duration_str)
        # 2 pass run
        bitrate = self.SIZE_LIMIT_GIF / duration * 1000000 * 8
        self._run_docker(
            client,
            f"-i {gif_url} {ffmpeg_options} -b:v {bitrate} -pass 1 -f mp4 /dev/null -y"
        )
        self._run_docker(
            client,
            f"-i {gif_url} {ffmpeg_options} -b:v {bitrate} -pass 2 {two_pass_filename} -y"
        )
        return two_pass_filename

    def _run_docker(self, client: DockerClient, args: str, entrypoint: Optional[str] = None) -> str:
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
            time.sleep(2)
        # Kill container
        logger.warning("Docker timed out, killing container.")
        container.kill()
        container.remove(force=True)
        raise TimeoutError("Docker container timed out")


class FAStatus:
    def __init__(
            self,
            online_guests: int,
            online_registered: int,
            online_other: int,
            online_total: int,
            server_time: datetime
    ):
        self.online_guests = online_guests
        self.online_registered = online_registered
        self.online_other = online_other
        self.online_total = online_total
        self.server_time = server_time

    @classmethod
    def from_dict(cls, status_dict: Dict[str, Union[str, Dict[str, int]]]) -> 'FAStatus':
        return FAStatus(
            status_dict["online"]["guests"],
            status_dict["online"]["registered"],
            status_dict["online"]["other"],
            status_dict["online"]["total"],
            dateutil.parser.parse(status_dict["fa_server_time_at"])
        )
