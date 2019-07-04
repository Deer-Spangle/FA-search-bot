import random
import string
from typing import Union, List

from fa_export_api import FAExportAPI, PageNotFound
from fa_submission import FASubmission


def _random_image_id(submission_id: int) -> int:
    return int(submission_id * 48.5 + random.randint(0, 13))


def _random_string() -> str:
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(random.randint(5, 20)))


class MockSubmission(FASubmission):

    def __init__(
            self,
            submission_id: Union[str, int],
            *,
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
        if file_ext in FASubmission.EXTENSIONS_PHOTO + ["gif"]:
            self._full_image_url = self._download_url
        else:
            self._full_image_url = self._download_url + ".jpg"
        self._download_file_size = file_size


class MockExportAPI(FAExportAPI):

    def __init__(self):
        super().__init__("--")
        self.submissions = {}
        self.user_folders = {}
        self.search_results = {}

    def with_submission(self, submission: FASubmission) -> 'MockExportAPI':
        self.submissions[submission.submission_id] = submission
        return self

    def with_submissions(self, list_submissions: List[FASubmission]) -> 'MockExportAPI':
        for submission in list_submissions:
            self.with_submission(submission)
        return self

    def with_gallery_pages(
            self,
            username: str,
            folder: str,
            list_submissions: List[FASubmission],
            page: int = 1
    ) -> 'MockExportAPI':
        if username not in self.user_folders:
            self.user_folders[username] = {}
        self.user_folders[username][f"{folder}:{page}"] = list_submissions
        self.with_submissions(list_submissions)
        return self

    def with_search_results(self, query: str, list_submissions: List[FASubmission], page: int = 1):
        self.search_results[f"{query}:{page}"] = list_submissions
        self.with_submissions(list_submissions)
        return self

    def get_full_submission(self, submission_id: str) -> FASubmission:
        if submission_id not in self.submissions:
            raise PageNotFound(f"Submission not found with ID: {submission_id}")
        return self.submissions[submission_id]

    def get_user_folder(self, user: str, folder: str, page: int = 1) -> List[FASubmission]:
        return self.user_folders[user][f"{folder}:{page}"]
