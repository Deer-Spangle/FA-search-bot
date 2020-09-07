import datetime
import unittest

import requests_mock

from fa_search_bot.fa_export_api import FAExportAPI, PageNotFound
from fa_search_bot.fa_submission import FASubmissionFull, FASubmissionShort
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder


class FAExportAPITest(unittest.TestCase):

    def test_constructor(self):
        api_url = "http://example.com/"

        api = FAExportAPI(api_url, ignore_status=True)

        assert api.base_url == "http://example.com"

    @requests_mock.mock()
    def test_api_request(self, r):
        api_url = "http://example.com/"
        path = "/resources/123"
        api = FAExportAPI(api_url, ignore_status=True)
        test_obj = {"key": "value"}
        r.get(
            "http://example.com/resources/123",
            json=test_obj
        )

        resp = api._api_request(path)

        assert resp.json() == test_obj

    @requests_mock.mock()
    def test_api_request_with_retry__does_not_retry_200(self, r):
        api_url = "http://example.com/"
        path = "/resources/200"
        api = FAExportAPI(api_url, ignore_status=True)
        test_obj = {"key": "value"}
        r.get(
            "http://example.com/resources/200",
            [
                {"json": test_obj, "status_code": 200},
                {"text": "500 Error. Something broke.", "status_code": 500},
            ]
        )

        start_time = datetime.datetime.now()
        resp = api._api_request_with_retry(path)
        end_time = datetime.datetime.now()

        time_waited = end_time - start_time
        assert time_waited.seconds <= 1
        assert resp.status_code == 200
        assert resp.json() == test_obj

    @requests_mock.mock()
    def test_api_request_with_retry__does_not_retry_400_error(self, r):
        api_url = "http://example.com/"
        path = "/resources/400"
        api = FAExportAPI(api_url, ignore_status=True)
        r.get(
            "http://example.com/resources/400",
            [
                {"text": "400 error, you messed up.", "status_code": 400},
                {"text": "500 Error. Something broke.", "status_code": 500},
            ]
        )

        start_time = datetime.datetime.now()
        resp = api._api_request_with_retry(path)
        end_time = datetime.datetime.now()

        time_waited = end_time - start_time
        assert time_waited.seconds <= 1
        assert resp.status_code == 400
        assert resp.text == "400 error, you messed up."

    @requests_mock.mock()
    def test_api_request_with_retry__retries_500_error(self, r):
        api_url = "http://example.com/"
        path = "/resources/500"
        api = FAExportAPI(api_url, ignore_status=True)
        test_obj = {"key": "value"}
        r.get(
            "http://example.com/resources/500",
            [
                {"text": "500 Error. Something broke.", "status_code": 500},
                {"text": "500 Error. Something broke.", "status_code": 500},
                {"json": test_obj, "status_code": 200}
            ]
        )

        start_time = datetime.datetime.now()
        resp = api._api_request_with_retry(path)
        end_time = datetime.datetime.now()

        time_waited = end_time - start_time
        assert 0.5 <= time_waited.seconds <= 5
        assert resp.status_code == 200
        assert resp.json() == test_obj

    @requests_mock.mock()
    def test_get_full_submission(self, r):
        builder = SubmissionBuilder(thumb_size=300)
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/submission/{builder.submission_id}.json",
            json=builder.build_submission_json()
        )

        submission = api.get_full_submission(builder.submission_id)

        assert isinstance(submission, FASubmissionFull)
        assert submission.submission_id == builder.submission_id
        assert submission.link == builder.link
        assert submission.thumbnail_url == builder.thumbnail_url.replace("@300-", "@1600-")
        assert submission.download_url == builder.download_url
        assert submission.full_image_url == builder.download_url

    @requests_mock.mock()
    def test_get_full_submission_fails(self, r):
        post_id = "45282"
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/submission/{post_id}.json",
            status_code=404
        )

        try:
            api.get_full_submission(post_id)
            assert False, "Should have thrown exception"
        except PageNotFound as e:
            assert str(e) == f"Submission not found with ID: {post_id}"

    @requests_mock.mock()
    def test_get_user_folder(self, r):
        post_id1 = "32342"
        post_id2 = "32337"
        builder1 = SubmissionBuilder(submission_id=post_id1)
        builder2 = SubmissionBuilder(submission_id=post_id2)
        username = "fender"
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/user/{username}/gallery.json?page=1&full=1",
            json=[
                builder1.build_search_json(),
                builder2.build_search_json()
            ]
        )

        results = api.get_user_folder(username, "gallery")

        assert len(results) == 2
        for result in results:
            assert isinstance(result, FASubmissionShort)
        assert results[0].submission_id == post_id1
        assert results[1].submission_id == post_id2
        assert results[0].link == f"https://furaffinity.net/view/{post_id1}/"
        assert results[1].link == f"https://furaffinity.net/view/{post_id2}/"
        assert results[0].thumbnail_url == builder1.thumbnail_url
        assert results[1].thumbnail_url == builder2.thumbnail_url

    @requests_mock.mock()
    def test_get_user_folder_scraps(self, r):
        builder = SubmissionBuilder()
        username = "citrinelle"
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/user/{username}/scraps.json?page=1&full=1",
            json=[
                builder.build_search_json()
            ]
        )

        results = api.get_user_folder(username, "scraps")

        assert len(results) == 1
        assert isinstance(results[0], FASubmissionShort)
        assert results[0].submission_id == builder.submission_id
        assert results[0].link == builder.link
        assert results[0].thumbnail_url == builder.thumbnail_url

    @requests_mock.mock()
    def test_get_user_folder_awkward_characters(self, r):
        builder = SubmissionBuilder()
        username = "l[i]s"
        safe_username = "l%5Bi%5Ds"
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/user/{safe_username}/gallery.json?page=1&full=1",
            json=[
                builder.build_search_json()
            ]
        )

        results = api.get_user_folder(username, "gallery")

        assert len(results) == 1
        assert isinstance(results[0], FASubmissionShort)
        assert results[0].submission_id == builder.submission_id
        assert results[0].link == builder.link
        assert results[0].thumbnail_url == builder.thumbnail_url

    @requests_mock.mock()
    def test_get_user_folder_specified_page(self, r):
        builder = SubmissionBuilder()
        username = "citrinelle"
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/user/{username}/gallery.json?page=2&full=1",
            json=[
                builder.build_search_json()
            ]
        )

        results = api.get_user_folder(username, "gallery", 2)

        assert len(results) == 1
        assert isinstance(results[0], FASubmissionShort)
        assert results[0].submission_id == builder.submission_id
        assert results[0].link == builder.link
        assert results[0].thumbnail_url == builder.thumbnail_url

    @requests_mock.mock()
    def test_get_user_folder_empty(self, r):
        username = "fender"
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/user/{username}/gallery.json?page=1&full=1",
            json=[]
        )

        results = api.get_user_folder(username, "gallery")

        assert len(results) == 0

    @requests_mock.mock()
    def test_get_user_folder_does_not_exist(self, r):
        username = "dont-real"
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/user/{username}/gallery.json?page=1&full=1",
            status_code=404
        )

        try:
            api.get_user_folder(username, "gallery")
            assert False, "Should have thrown exception"
        except PageNotFound as e:
            assert str(e) == f"User not found by name: {username}"

    @requests_mock.mock()
    def test_get_user_folder_blank_username(self, r):
        username = ""
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/user/{username}/gallery.json?page=1&full=1",
            json={
                "id": None,
                "name": "gallery",
                "profile": "https://www.furaffinity.net/user/gallery/"
            }
        )

        try:
            api.get_user_folder(username, "gallery")
            assert False, "Should have thrown exception"
        except PageNotFound as e:
            assert str(e) == f"User not found by name: {username}"

    @requests_mock.mock()
    def test_get_search_results(self, r):
        post_id1 = "32342"
        post_id2 = "32337"
        builder1 = SubmissionBuilder(submission_id=post_id1)
        builder2 = SubmissionBuilder(submission_id=post_id2)
        search = "deer"
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/search.json?full=1&perpage=48&q={search}&page=1",
            json=[
                builder1.build_search_json(),
                builder2.build_search_json()
            ]
        )

        results = api.get_search_results(search)

        assert len(results) == 2
        assert isinstance(results[0], FASubmissionShort)
        assert isinstance(results[1], FASubmissionShort)
        assert results[0].submission_id == post_id1
        assert results[1].submission_id == post_id2
        assert results[0].link == f"https://furaffinity.net/view/{post_id1}/"
        assert results[1].link == f"https://furaffinity.net/view/{post_id2}/"
        assert results[0].thumbnail_url == builder1.thumbnail_url
        assert results[1].thumbnail_url == builder2.thumbnail_url

    @requests_mock.mock()
    def test_get_search_results_with_space(self, r):
        builder = SubmissionBuilder()
        search = "deer lion"
        search_safe = "deer%20lion"
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/search.json?full=1&perpage=48&q={search_safe}&page=1",
            json=[
                builder.build_search_json()
            ]
        )

        results = api.get_search_results(search)

        assert len(results) == 1
        assert isinstance(results[0], FASubmissionShort)
        assert results[0].submission_id == builder.submission_id

    @requests_mock.mock()
    def test_get_search_results_with_extended_modifiers(self, r):
        builder = SubmissionBuilder()
        search = "(deer & !lion) | (goat & !tiger)"
        search_safe = "(deer%20&%20!lion)%20%7C%20(goat%20&%20!tiger)"
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/search.json?full=1&perpage=48&q={search_safe}&page=1",
            json=[
                builder.build_search_json()
            ]
        )

        results = api.get_search_results(search)

        assert len(results) == 1
        assert isinstance(results[0], FASubmissionShort)
        assert results[0].submission_id == builder.submission_id

    @requests_mock.mock()
    def test_get_search_results_specified_page(self, r):
        builder = SubmissionBuilder()
        search = "deer"
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/search.json?full=1&perpage=48&q={search}&page=2",
            json=[
                builder.build_search_json()
            ]
        )

        results = api.get_search_results(search, 2)

        assert len(results) == 1
        assert isinstance(results[0], FASubmissionShort)
        assert results[0].submission_id == builder.submission_id

    @requests_mock.mock()
    def test_get_search_results_no_results(self, r):
        search = "chital_deer"
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/search.json?full=1&perpage=48&q={search}&page=1",
            json=[
            ]
        )

        results = api.get_search_results(search)

        assert len(results) == 0

    @requests_mock.mock()
    def test_get_browse_page_default_1(self, r):
        builder = SubmissionBuilder()
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/browse.json?page=1",
            json=[
                builder.build_search_json()
            ]
        )

        results = api.get_browse_page()

        assert len(results) == 1
        assert isinstance(results[0], FASubmissionShort)
        assert results[0].submission_id == builder.submission_id

    @requests_mock.mock()
    def test_get_browse_page_specify_page(self, r):
        builder = SubmissionBuilder()
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/browse.json?page=5",
            json=[
                builder.build_search_json()
            ]
        )

        results = api.get_browse_page(5)

        assert len(results) == 1
        assert isinstance(results[0], FASubmissionShort)
        assert results[0].submission_id == builder.submission_id

    @requests_mock.mock()
    def test_get_browse_page_no_results(self, r):
        post_id = "32342"
        api = FAExportAPI("http://example.com/", ignore_status=True)
        r.get(
            f"http://example.com/browse.json?page=5",
            json=[
            ]
        )

        results = api.get_browse_page(5)

        assert len(results) == 0

    @requests_mock.mock()
    def test_get_status_before_submission(self, r):
        builder = SubmissionBuilder(thumb_size=300)
        api = FAExportAPI("http://example.com/")
        r.get(
            "http://example.com/status.json",
            json={
                "online": {
                    "guests": 17,
                    "registered": api.STATUS_LIMIT_REGISTERED-1,
                    "other": 12,
                    "total": api.STATUS_LIMIT_REGISTERED + 28
                },
                "fa_server_time_at": "2020-09-08T00:13:14Z"
            }
        )
        r.get(
            f"http://example.com/submission/{builder.submission_id}.json",
            json=builder.build_submission_json()
        )

        submission = api.get_full_submission(builder.submission_id)

        assert api.last_status_check is not None
        assert api.slow_down_status is False
        assert isinstance(submission, FASubmissionFull)
        assert submission.submission_id == builder.submission_id
        assert submission.link == builder.link
        assert submission.thumbnail_url == builder.thumbnail_url.replace("@300-", "@1600-")
        assert submission.download_url == builder.download_url
        assert submission.full_image_url == builder.download_url

    @requests_mock.mock()
    def test_get_status_api_retry(self, r):
        api_url = "http://example.com/"
        path = "/resources/200"
        api = FAExportAPI(api_url, ignore_status=True)
        test_obj = {"key": "value"}
        r.get(
            "http://example.com/status.json",
            json={
                "online": {
                    "guests": 17,
                    "registered": api.STATUS_LIMIT_REGISTERED-1,
                    "other": 12,
                    "total": api.STATUS_LIMIT_REGISTERED + 28
                },
                "fa_server_time_at": "2020-09-08T00:13:14Z"
            }
        )
        r.get(
            "http://example.com/resources/200",
            [
                {"json": test_obj, "status_code": 200},
            ]
        )

        resp = api._api_request_with_retry(path)

        assert api.last_status_check is not None
        assert api.slow_down_status is False
        assert resp.status_code == 200
        assert resp.json() == test_obj

    @requests_mock.mock()
    def test_get_status_turns_on_slowdown(self, r):
        api_url = "http://example.com/"
        path = "/resources/200"
        api = FAExportAPI(api_url, ignore_status=True)
        test_obj = {"key": "value"}
        r.get(
            "http://example.com/status.json",
            json={
                "online": {
                    "guests": 17,
                    "registered": api.STATUS_LIMIT_REGISTERED+1,
                    "other": 12,
                    "total": api.STATUS_LIMIT_REGISTERED + 30
                },
                "fa_server_time_at": "2020-09-08T00:13:14Z"
            }
        )
        r.get(
            "http://example.com/resources/200",
            [
                {"json": test_obj, "status_code": 200},
            ]
        )

        start_time = datetime.datetime.now()
        resp = api._api_request_with_retry(path)
        end_time = datetime.datetime.now()

        assert api.last_status_check is not None
        assert api.slow_down_status is True
        time_waited = end_time - start_time
        assert time_waited.seconds >= 1
        assert resp.status_code == 200
        assert resp.json() == test_obj
