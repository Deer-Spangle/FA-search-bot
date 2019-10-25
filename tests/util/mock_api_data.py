import random
from abc import ABC
from typing import Union, List

from fa_submission import FAUser, FAUserShort, FASubmission, FASubmissionFull
from tests.util.mock_export_api import _random_string, _random_image_id


class MockAPIData(ABC):

    @staticmethod
    def browse():
        return MockAPIDataListing()

    @staticmethod
    def search():
        return MockAPIDataListing()

    @staticmethod
    def gallery():
        profile_name = _random_string()
        author = FAUserShort(profile_name.title(), profile_name)
        return MockAPIDataListing(author=author)

    @staticmethod
    def favs():
        profile_name = _random_string()
        author = FAUserShort(profile_name.title(), profile_name)
        return MockAPIDataListing(author=author, favs=True)


class SubmissionBuilder:

    def __init__(
            self,
            *,
            submission_id: Union[str, int] = None,
            username: str = None,
            image_id: int = None,
            file_size: int = 14852,
            file_ext: str = "jpg",
            fav_id: str = None,
            title: str = None,
            author: FAUser = None,
            description: str = None,
            keywords: List[str] = None
    ):
        if submission_id is None:
            submission_id = random.randint(10_000, 100_000)
        submission_id = str(submission_id)
        # Internal variables
        if image_id is None:
            image_id = _random_image_id(int(submission_id))
        if username is None:
            username = _random_string()
        if fav_id is None:
            fav_id = str(_random_image_id(int(submission_id)))
        folder = ""
        if file_ext in FASubmission.EXTENSIONS_AUDIO:
            folder = "music/"
        if file_ext in FASubmission.EXTENSIONS_DOCUMENT:
            folder = "stories/"
        # Variables for superclass
        thumbnail_url = f"https://t.facdn.net/{submission_id}@1600-{image_id}.jpg"
        download_url = f"https://d.facdn.net/art/{username}/{folder}{image_id}/" \
            f"{image_id}.{username}_{_random_string()}.{file_ext}"
        if file_ext in FASubmission.EXTENSIONS_PHOTO + ["gif"]:
            full_image_url = download_url
        else:
            full_image_url = download_url + ".jpg"
        if title is None:
            title = _random_string()
        if author is None:
            profile_name = _random_string()
            author = FAUser.from_submission_dict({"name": profile_name.title(), "profile_name": profile_name})
        if description is None:
            description = _random_string() * 5
        if keywords is None:
            keywords = [_random_string() for _ in range(3)]
        # Super
        self.submission_id = submission_id
        self.link = f"https://furaffinity.net/view/{submission_id}/"
        self.thumbnail_url = thumbnail_url
        self.title = title
        self.author = author
        self.download_url = download_url
        self.full_image_url = full_image_url
        self.description = description
        self.keywords = keywords
        self._download_file_size = None
        self.fav_id = fav_id
        self._download_file_size = file_size

    def build_full_submission(self):
        return FASubmissionFull(
            self.submission_id,
            self.thumbnail_url,
            self.download_url,
            self.full_image_url,
            self.title,
            self.author,
            self.description,
            self.keywords
        )

    def build_mock_submission(self):
        pass  # TODO

    def build_submission_json(self):
        return {
            "title": self.title,
            "description": self.description,
            "description_body": self.description,
            "name": self.author.name,
            "profile": self.author.link,
            "profile_name": self.author.profile_name,
            "link": f"https://www.furaffinity.net/view/{self.submission_id}/",
            "download": self.download_url,
            "full": self.full_image_url,
            "thumbnail": self.thumbnail_url,
            "keywords": self.keywords
        }

    def build_search_json(self):
        pass  # TODO
