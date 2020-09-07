import logging
import time
import datetime
from typing import List

import requests

from fa_search_bot.fa_submission import FASubmission, FASubmissionShort, FASubmissionFull, FASubmissionShortFav, \
    FAStatus

logger = logging.getLogger("fa_search_bot.fa_export_api")


class PageNotFound(Exception):
    pass


class FAExportAPI:
    MAX_RETRIES = 7
    STATUS_CHECK_BACKOFF = 60 * 5
    STATUS_LIMIT_REGISTERED = 10_000
    SLOWDOWN_BACKOFF = 1

    def __init__(self, base_url: str, ignore_status = False):
        self.base_url = base_url.rstrip("/")
        self.last_status_check = None
        self.slow_down_status = False
        self.ignore_status = ignore_status

    def _api_request(self, path: str) -> requests.Response:
        path = path.lstrip("/")
        return requests.get(f"{self.base_url}/{path}")

    def _api_request_with_retry(self, path: str) -> requests.Response:
        if self._is_site_slowdown():
            time.sleep(self.SLOWDOWN_BACKOFF)
        resp = self._api_request(path)
        for tries in range(self.MAX_RETRIES):
            if str(resp.status_code)[0] != "5":
                return resp
            time.sleep(tries ** 2)
            resp = self._api_request(path)
        return resp

    def _is_site_slowdown(self) -> bool:
        if self.ignore_status:
            return False
        now = datetime.datetime.now()
        if (
                self.last_status_check is None
                or (self.last_status_check + datetime.timedelta(seconds=self.STATUS_CHECK_BACKOFF)) < now
        ):
            status = self.status()
            self.last_status_check = now
            self.slow_down_status = status.online_registered > self.STATUS_LIMIT_REGISTERED
        return self.slow_down_status

    def get_full_submission(self, submission_id: str) -> FASubmissionFull:
        logger.debug("Getting full submission for submission ID %s", submission_id)
        sub_resp = self._api_request_with_retry(f"submission/{submission_id}.json")
        # If API returns fine
        if sub_resp.status_code == 200:
            submission = FASubmission.from_full_dict(sub_resp.json())
            return submission
        else:
            raise PageNotFound(f"Submission not found with ID: {submission_id}")

    def get_user_folder(self, user: str, folder: str, page: int = 1) -> List[FASubmissionShort]:
        logger.debug("Getting user folder for user %s, folder %s, and page %s", user, folder, page)
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
            logger.warning("User gallery not found with name: %s", user)
            raise PageNotFound(f"User not found by name: {user}")

    def get_user_favs(self, user: str, next_id: str = None) -> List[FASubmissionShortFav]:
        logger.debug("Getting user favourites for user: %s, next_id: %s", user, next_id)
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
            logger.warning("User favourites not found with name: %s", user)
            raise PageNotFound(f"User not found by name: {user}")

    def get_search_results(self, query: str, page: int = 1) -> List[FASubmissionShort]:
        logger.debug("Searching for query: %s, page: %s", query, page)
        resp = self._api_request_with_retry(f"search.json?full=1&perpage=48&q={query}&page={page}")
        data = resp.json()
        submissions = []
        for submission_data in data:
            submissions.append(FASubmission.from_short_dict(submission_data))
        return submissions

    def get_browse_page(self, page: int = 1) -> List[FASubmissionShort]:
        logger.debug("Getting browse page %s", page)
        resp = self._api_request_with_retry(f"browse.json?page={page}")
        data = resp.json()
        submissions = []
        for submission_data in data:
            submissions.append(FASubmission.from_short_dict(submission_data))
        return submissions

    def status(self) -> FAStatus:
        logger.debug("Getting status page")
        path = "status.json"
        resp = self._api_request(path)
        for tries in range(self.MAX_RETRIES):
            if str(resp.status_code)[0] != "5":
                break
            resp = self._api_request(path)
        data = resp.json()
        return FAStatus.from_dict(data)
