import random
import string
from typing import Union

from fa_submission import FASubmission


def _random_image_id(submission_id: int) -> int:
    return int(submission_id * 48.5 + random.randint(0, 13))


def _random_string() -> str:
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(random.randint(5, 20)))


class MockSubmission(FASubmission):

    def __init__(
            self,
            submission_id: Union[str, int],
            username: str = None,
            image_id: int = None,
            file_size=14852,
            file_ext="jpg"):
        super().__init__(str(submission_id))
        if image_id is None:
            image_id = _random_image_id(int(submission_id))
        if username is None:
            username = _random_string()
        folder = ""
        if file_ext in FASubmission.EXTENSIONS_AUDIO:
            folder = "music/"
        if file_ext in FASubmission.EXTENSIONS_DOCUMENT:
            folder = "stories/"
        # Setup variables
        self.link = f"https://www.furaffinity.net/view/{submission_id}/"
        self._thumbnail_url = f"https://t.facdn.net/{submission_id}@1600-{image_id}.jpg"
        self._download_url = f"https://d.facdn.net/art/{username}/{folder}{image_id}/" \
            f"{image_id}.{username}_{_random_string()}.{file_ext}"
        if file_ext in FASubmission.EXTENSIONS_PHOTO:
            self._full_image_url = self._download_url
        else:
            self._full_image_url = self._download_url + ".jpg"
        self._download_file_size = file_size
