import random
import string
from typing import Union, List

from fa_export_api import FAExportAPI, PageNotFound
from fa_submission import FASubmission, FASubmissionFull


def _random_image_id(submission_id: int) -> int:
    return int(submission_id * 48.5 + random.randint(0, 13))


def _random_string() -> str:
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(random.randint(5, 20)))


class MockSubmission(FASubmissionFull):

    def __init__(
            self,
            submission_id: Union[str, int],
            *,
            username: str = None,
            image_id: int = None,
            file_size: int = 14852,
            file_ext: str = "jpg",
            fav_id: str = None
    ):
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
        # Super
        super().__init__(str(submission_id), thumbnail_url, download_url, full_image_url)
        self.fav_id = fav_id
        self._download_file_size = file_size


class MockExportAPI(FAExportAPI):

    def __init__(self):
        super().__init__("--")
        self.submissions = {}
        self.user_folders = {}
        self.search_results = {}
        self.browse_results = {}

    def with_submission(self, submission: MockSubmission) -> 'MockExportAPI':
        self.submissions[submission.submission_id] = submission
        return self

    def with_submissions(self, list_submissions: List[MockSubmission]) -> 'MockExportAPI':
        for submission in list_submissions:
            self.with_submission(submission)
        return self

    def with_user_folder(
            self,
            username: str,
            folder: str,
            list_submissions: List[MockSubmission],
            page: int = 1
    ) -> 'MockExportAPI':
        if username not in self.user_folders:
            self.user_folders[username] = {}
        self.user_folders[username][f"{folder}:{page}"] = list_submissions
        self.with_submissions(list_submissions)
        return self

    def with_user_favs(
            self, username: str, list_submissions: List[MockSubmission], next_id: str = None
    ) -> 'MockExportAPI':
        if username not in self.user_folders:
            self.user_folders[username] = {}
        self.user_folders[username][f"favs:{next_id}"] = list_submissions
        self.with_submissions(list_submissions)
        return self

    def with_search_results(self, query: str, list_submissions: List[MockSubmission], page: int = 1):
        self.search_results[f"{query.lower()}:{page}"] = list_submissions
        self.with_submissions(list_submissions)
        return self

    def with_browse_results(self, list_submissions: List[MockSubmission], page: int = 1):
        self.browse_results[page] = list_submissions
        self.with_submissions(list_submissions)
        return self

    def get_full_submission(self, submission_id: str) -> FASubmission:
        if submission_id not in self.submissions:
            raise PageNotFound(f"Submission not found with ID: {submission_id}")
        return self.submissions[submission_id]

    def get_user_folder(self, user: str, folder: str, page: int = 1) -> List[FASubmission]:
        if user not in self.user_folders:
            return []
        if f"{folder}:{page}" not in self.user_folders[user]:
            return []
        return self.user_folders[user][f"{folder}:{page}"]

    def get_user_favs(self, user: str, next_id: int = 1) -> List[FASubmission]:
        if user not in self.user_folders:
            return []
        if f"favs:{next_id}" not in self.user_folders[user]:
            return []
        return self.user_folders[user][f"favs:{next_id}"]

    def get_search_results(self, query: str, page: int = 1) -> List[FASubmission]:
        if f"{query.lower()}:{page}" not in self.search_results:
            return []
        return self.search_results[f"{query.lower()}:{page}"]

    def get_browse_page(self, page: int = 1) -> List[FASubmission]:
        if page not in self.browse_results:
            return []
        return self.browse_results[page]
