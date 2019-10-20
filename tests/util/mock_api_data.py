import random
from abc import ABC

from fa_submission import FAUser, FAUserShort
from tests.util.mock_export_api import _random_string, _random_image_id


class MockAPIData(ABC):

    @staticmethod
    def submission():
        return MockAPIDataSubmission()

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


class MockAPIDataSubmission:

    def __init__(self):
        self.title = f"Example {_random_string()}"
        self.description = _random_string() * 5
        profile_name = _random_string()
        self.author = FAUser.from_submission_dict({"name": profile_name.title(), "profile_name": profile_name})
        self.sub_id = random.randint(10_000_000, 30_000_000)
        self.image_id = _random_image_id(self.sub_id)
        self.download_link = f"http://d.facdn.net/art/{self.author.profile_name}/1284661300/1284661300.fender_fender.png"
        self.full_link = self.download_link
        self.thumbnail_link = f"http://t.facdn.net/{self.sub_id}@400-{self.image_id}.jpg"
        self.keywords = ["Example", "test"] + [_random_string() for _ in range(3)]

    def with_sub_id(self, sub_id):
        self.sub_id = sub_id
        self.image_id = _random_image_id(self.sub_id)
        self.download_link = f"http://d.facdn.net/art/{self.author.profile_name}/1284661300/1284661300.fender_fender.png"
        self.full_link = self.download_link
        self.thumbnail_link = f"http://t.facdn.net/{self.sub_id}@400-{self.image_id}.jpg"

    def build(self):
        return {
            "title": self.title,
            "description": self.description,
            "description_body": self.description,
            "name": self.author.name,
            "profile": self.author.link,
            "profile_name": self.author.profile_name,
            "link": f"https://www.furaffinity.net/view/{self.sub_id}/",
            "download": self.download_link,
            "full": self.full_link,
            "thumbnail": self.thumbnail_link,
            "keywords": self.keywords
        }
