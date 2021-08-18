import asyncio
import enum
import logging
import datetime
from typing import List

import requests
from prometheus_client import Counter, Enum, Histogram

from fa_search_bot.sites.fa_submission import FASubmission, FASubmissionShort, FASubmissionFull, FASubmissionShortFav, \
    FAStatus

logger = logging.getLogger(__name__)

site_slowdown = Enum(
    "fasearchbot_faapi_slowdown_state",
    "Whether the FA API is in a slow state due to high number of registered users on FA",
    states=["slow", "not_slow"]
)
cloudflare_errors = Counter(
    "fasearchbot_faapi_cloudflare_errors_total",
    "Number of cloudflare errors received by the FA API",
    labelnames=["endpoint"]
)
api_request_times = Histogram(
    "fasearchbot_faapi_request_time_seconds",
    "Request times of the FA API, in seconds",
    labelnames=["endpoint"]
)
api_retry_counts = Histogram(
    "fasearchbot_faapi_retry_counts",
    "Retry counts of the FA API",
    buckets=list(range(10)),
    labelnames=["endpoint"]
)


class APIException(Exception):
    pass


class PageNotFound(APIException):
    pass


class CloudflareError(APIException):
    pass


class Endpoint(enum.Enum):
    SUBMISSION = "submission"
    USER_FOLDER = "user_folder"
    USER_FAVS = "user_favs"
    SEARCH = "search"
    BROWSE = "browse"
    STATUS = "status"


class FAExportAPI:
    MAX_RETRIES = 7
    STATUS_CHECK_BACKOFF = 60 * 5
    STATUS_LIMIT_REGISTERED = 10_000
    SLOWDOWN_BACKOFF = 1

    def __init__(self, base_url: str, ignore_status: bool = False):
        self.base_url = base_url.rstrip("/")
        self.last_status_check = None
        self.slow_down_status = False
        self.ignore_status = ignore_status
        for endpoint in Endpoint:
            cloudflare_errors.labels(endpoint=endpoint.value)
            api_request_times.labels(endpoint=endpoint.value)
            api_retry_counts.labels(endpoint=endpoint.value)

    def _api_request(self, path: str, endpoint_label: Endpoint) -> requests.Response:
        path = path.lstrip("/")
        with api_request_times.labels(endpoint=endpoint_label.value).time():
            resp = requests.get(f"{self.base_url}/{path}")
        if resp.status_code == 503:
            cloudflare_errors.labels(endpoint=endpoint_label.value).inc()
            raise CloudflareError()
        return resp

    async def _api_request_with_retry(self, path: str, endpoint_label: Endpoint) -> requests.Response:
        if self._is_site_slowdown():
            await asyncio.sleep(self.SLOWDOWN_BACKOFF)
        resp = self._api_request(path, endpoint_label)
        tries = 0
        for tries in range(self.MAX_RETRIES):
            if str(resp.status_code)[0] != "5":
                api_retry_counts.labels(endpoint=endpoint_label.value).observe(tries)
                return resp
            await asyncio.sleep(tries ** 2)
            resp = self._api_request(path, endpoint_label)
        api_retry_counts.labels(endpoint=endpoint_label.value).observe(tries)
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
        site_slowdown.state("slow" if self.slow_down_status else "not_slow")
        return self.slow_down_status

    async def get_full_submission(self, submission_id: str) -> FASubmissionFull:
        logger.debug("Getting full submission for submission ID %s", submission_id)
        sub_resp = await self._api_request_with_retry(f"submission/{submission_id}.json", Endpoint.SUBMISSION)
        # If API returns fine
        if sub_resp.status_code == 200:
            submission = FASubmission.from_full_dict(sub_resp.json())
            return submission
        else:
            raise PageNotFound(f"Submission not found with ID: {submission_id}")

    async def get_user_folder(self, user: str, folder: str, page: int = 1) -> List[FASubmissionShort]:
        logger.debug("Getting user folder for user %s, folder %s, and page %s", user, folder, page)
        if user.strip() == "":
            raise PageNotFound(f"User not found by name: {user}")
        resp = await self._api_request_with_retry(f"user/{user}/{folder}.json?page={page}&full=1", Endpoint.USER_FOLDER)
        if resp.status_code == 200:
            data = resp.json()
            submissions = []
            for submission_data in data:
                submissions.append(FASubmission.from_short_dict(submission_data))
            return submissions
        else:
            logger.warning("User gallery not found with name: %s", user)
            raise PageNotFound(f"User not found by name: {user}")

    async def get_user_favs(self, user: str, next_id: str = None) -> List[FASubmissionShortFav]:
        logger.debug("Getting user favourites for user: %s, next_id: %s", user, next_id)
        if user.strip() == "":
            raise PageNotFound(f"User not found by name: {user}")
        next_str = ""
        if next_id is not None:
            next_str = f"next={next_id}&"
        resp = await self._api_request_with_retry(f"user/{user}/favorites.json?{next_str}full=1", Endpoint.USER_FAVS)
        if resp.status_code == 200:
            data = resp.json()
            submissions = []
            for submission_data in data:
                submissions.append(FASubmission.from_short_dict(submission_data))
            return submissions
        else:
            logger.warning("User favourites not found with name: %s", user)
            raise PageNotFound(f"User not found by name: {user}")

    async def get_search_results(self, query: str, page: int = 1) -> List[FASubmissionShort]:
        logger.debug("Searching for query: %s, page: %s", query, page)
        resp = await self._api_request_with_retry(
            f"search.json?full=1&perpage=48&q={query}&page={page}",
            Endpoint.SEARCH
        )
        data = resp.json()
        submissions = []
        for submission_data in data:
            submissions.append(FASubmission.from_short_dict(submission_data))
        return submissions

    async def get_browse_page(self, page: int = 1) -> List[FASubmissionShort]:
        logger.debug("Getting browse page %s", page)
        resp = await self._api_request_with_retry(f"browse.json?page={page}", Endpoint.BROWSE)
        data = resp.json()
        submissions = []
        for submission_data in data:
            submissions.append(FASubmission.from_short_dict(submission_data))
        return submissions

    def status(self) -> FAStatus:
        logger.debug("Getting status page")
        path = "status.json"
        resp = self._api_request(path, Endpoint.STATUS)
        for tries in range(self.MAX_RETRIES):
            if str(resp.status_code)[0] != "5":
                break
            resp = self._api_request(path, Endpoint.STATUS)
        data = resp.json()
        return FAStatus.from_dict(data)
