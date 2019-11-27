import time
from typing import List

import requests

from fa_submission import FASubmission, FASubmissionShort, FASubmissionFull, FASubmissionShortFav


class PageNotFound(Exception):
    pass


class FAExportAPI:
    MAX_RETRIES = 7

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _api_request(self, path: str) -> requests.Response:
        path = path.lstrip("/")
        return requests.get(f"{self.base_url}/{path}")

    def _api_request_with_retry(self, path: str) -> requests.Response:
        resp = self._api_request(path)
        for tries in range(self.MAX_RETRIES):
            if str(resp.status_code)[0] != "5":
                return resp
            time.sleep(tries ** 2)
            resp = self._api_request(path)
        return resp

    def get_full_submission(self, submission_id: str) -> FASubmissionFull:
        sub_resp = self._api_request_with_retry(f"submission/{submission_id}.json")
        # If API returns fine
        if sub_resp.status_code == 200:
            submission = FASubmission.from_full_dict(sub_resp.json())
            return submission
        else:
            raise PageNotFound(f"Submission not found with ID: {submission_id}")

    def get_user_folder(self, user: str, folder: str, page: int = 1) -> List[FASubmissionShort]:
        if user.strip() == "":
            raise PageNotFound(f"User not found by name: {user}")
        resp = self._api_request_with_retry(f"user/{user}/{folder}.json?page={page}&full=1")
        if resp.status_code == 200:
            data = resp.json()
            submissions = []
            for submission_data in data:
                submissions.append(FASubmission.from_short_dict(submission_data))
            return submissions
        else:
            raise PageNotFound(f"User not found by name: {user}")

    def get_user_favs(self, user: str, next_id: str = None) -> List[FASubmissionShortFav]:
        if user.strip() == "":
            raise PageNotFound(f"User not found by name: {user}")
        next_str = ""
        if next_id is not None:
            next_str = f"next={next_id}&"
        resp = self._api_request_with_retry(f"user/{user}/favorites.json?{next_str}full=1")
        if resp.status_code == 200:
            data = resp.json()
            submissions = []
            for submission_data in data:
                submissions.append(FASubmission.from_short_dict(submission_data))
            return submissions
        else:
            raise PageNotFound(f"User not found by name: {user}")

    def get_search_results(self, query: str, page: int = 1) -> List[FASubmissionShort]:
        resp = self._api_request_with_retry(f"search.json?full=1&perpage=48&q={query}&page={page}")
        data = resp.json()
        submissions = []
        for submission_data in data:
            submissions.append(FASubmission.from_short_dict(submission_data))
        return submissions

    def get_browse_page(self, page: int = 1) -> List[FASubmissionShort]:
        resp = self._api_request_with_retry(f"browse.json?page={page}")
        data = resp.json()
        submissions = []
        for submission_data in data:
            submissions.append(FASubmission.from_short_dict(submission_data))
        return submissions
