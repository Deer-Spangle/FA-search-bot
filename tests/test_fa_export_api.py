import unittest

import requests_mock

from fa_export_api import FAExportAPI, PageNotFound
from fa_submission import FASubmissionFull, FASubmissionShort


class FAExportAPITest(unittest.TestCase):

    def test_constructor(self):
        api_url = "http://example.com/"

        api = FAExportAPI(api_url)

        assert api.base_url == "http://example.com"

    @requests_mock.mock()
    def test_api_request(self, r):
        api_url = "http://example.com/"
        path = "/resources/123"
        api = FAExportAPI(api_url)
        test_obj = {"key": "value"}
        r.get(
            "http://example.com/resources/123",
            json=test_obj
        )

        resp = api._api_request(path)

        assert resp.json() == test_obj

    @requests_mock.mock()
    def test_get_full_submission(self, r):
        post_id = "45282"
        api = FAExportAPI("http://example.com/")
        link = f"https://furaffinity.net/view/{post_id}/"
        thumb = f"https://t.facdn.net/{post_id}@300-1562366073.jpg"
        download = f"https://d.facdn.net/art/fender/{post_id}/{post_id}.fender_02edf64e.png"
        r.get(
            f"http://example.com/submission/{post_id}.json",
            json={
                "link": link,
                "thumbnail": thumb,
                "download": download,
                "full": download
            }
        )

        submission = api.get_full_submission(post_id)

        assert isinstance(submission, FASubmissionFull)
        assert submission.submission_id == post_id
        assert submission.link == link
        assert submission.thumbnail_url == thumb.replace(f"{post_id}@300-", f"{post_id}@1600-")
        assert submission.download_url == download
        assert submission.full_image_url == download

    @requests_mock.mock()
    def test_get_full_submission_fails(self, r):
        post_id = "45282"
        api = FAExportAPI("http://example.com/")
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
        thumb1 = f"https://t.facdn.net/{post_id1}@1600-1562366051.jpg"
        thumb2 = f"https://t.facdn.net/{post_id2}@1600-1562366073.jpg"
        username = "fender"
        api = FAExportAPI("http://example.com/")
        r.get(
            f"http://example.com/user/{username}/gallery.json?page=1&full=1",
            json=[
                {
                    "id": post_id1,
                    "thumbnail": thumb1
                },
                {
                    "id": post_id2,
                    "thumbnail": thumb2
                }
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
        assert results[0].thumbnail_url == thumb1
        assert results[1].thumbnail_url == thumb2

    @requests_mock.mock()
    def test_get_user_folder_scraps(self, r):
        post_id = "32342"
        thumb = f"https://t.facdn.net/{post_id}@1600-1562366051.jpg"
        username = "citrinelle"
        api = FAExportAPI("http://example.com/")
        r.get(
            f"http://example.com/user/{username}/scraps.json?page=1&full=1",
            json=[
                {
                    "id": post_id,
                    "thumbnail": thumb
                }
            ]
        )

        results = api.get_user_folder(username, "scraps")

        assert len(results) == 1
        assert isinstance(results[0], FASubmissionShort)
        assert results[0].submission_id == post_id
        assert results[0].link == f"https://furaffinity.net/view/{post_id}/"
        assert results[0].thumbnail_url == thumb

    @requests_mock.mock()
    def test_get_user_folder_awkward_characters(self, r):
        post_id = "89452"
        thumb = f"https://t.facdn.net/{post_id}@1600-1562366051.jpg"
        username = "l[i]s"
        safe_username = "l%5Bi%5Ds"
        api = FAExportAPI("http://example.com/")
        r.get(
            f"http://example.com/user/{safe_username}/gallery.json?page=1&full=1",
            json=[
                {
                    "id": post_id,
                    "thumbnail": thumb
                }
            ]
        )

        results = api.get_user_folder(username, "gallery")

        assert len(results) == 1
        assert isinstance(results[0], FASubmissionShort)
        assert results[0].submission_id == post_id
        assert results[0].link == f"https://furaffinity.net/view/{post_id}/"
        assert results[0].thumbnail_url == thumb

    @requests_mock.mock()
    def test_get_user_folder_specified_page(self, r):
        post_id = "32342"
        thumb = f"https://t.facdn.net/{post_id}@1600-1562366051.jpg"
        username = "citrinelle"
        api = FAExportAPI("http://example.com/")
        r.get(
            f"http://example.com/user/{username}/gallery.json?page=2&full=1",
            json=[
                {
                    "id": post_id,
                    "thumbnail": thumb
                }
            ]
        )

        results = api.get_user_folder(username, "gallery", 2)

        assert len(results) == 1
        assert isinstance(results[0], FASubmissionShort)
        assert results[0].submission_id == post_id
        assert results[0].link == f"https://furaffinity.net/view/{post_id}/"
        assert results[0].thumbnail_url == thumb

    @requests_mock.mock()
    def test_get_user_folder_empty(self, r):
        username = "fender"
        api = FAExportAPI("http://example.com/")
        r.get(
            f"http://example.com/user/{username}/gallery.json?page=1&full=1",
            json=[]
        )

        results = api.get_user_folder(username, "gallery")

        assert len(results) == 0

    @requests_mock.mock()
    def test_get_user_folder_does_not_exist(self, r):
        username = "dont-real"
        api = FAExportAPI("http://example.com/")
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
        api = FAExportAPI("http://example.com/")
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
        thumb1 = f"https://t.facdn.net/{post_id1}@1600-1562366051.jpg"
        thumb2 = f"https://t.facdn.net/{post_id2}@1600-1562366073.jpg"
        search = "deer"
        api = FAExportAPI("http://example.com/")
        r.get(
            f"http://example.com/search.json?full=1&perpage=48&q={search}&page=1",
            json=[
                {
                    "id": post_id1,
                    "thumbnail": thumb1
                },
                {
                    "id": post_id2,
                    "thumbnail": thumb2
                }
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
        assert results[0].thumbnail_url == thumb1
        assert results[1].thumbnail_url == thumb2

    @requests_mock.mock()
    def test_get_search_results_with_space(self, r):
        post_id = "32342"
        thumb = f"https://t.facdn.net/{post_id}@1600-1562366051.jpg"
        search = "deer lion"
        search_safe = "deer%20lion"
        api = FAExportAPI("http://example.com/")
        r.get(
            f"http://example.com/search.json?full=1&perpage=48&q={search_safe}&page=1",
            json=[
                {
                    "id": post_id,
                    "thumbnail": thumb
                }
            ]
        )

        results = api.get_search_results(search)

        assert len(results) == 1
        assert isinstance(results[0], FASubmissionShort)
        assert results[0].submission_id == post_id

    @requests_mock.mock()
    def test_get_search_results_with_extended_modifiers(self, r):
        post_id = "32342"
        thumb = f"https://t.facdn.net/{post_id}@1600-1562366051.jpg"
        search = "(deer & !lion) | (goat & !tiger)"
        search_safe = "(deer%20&%20!lion)%20%7C%20(goat%20&%20!tiger)"
        api = FAExportAPI("http://example.com/")
        r.get(
            f"http://example.com/search.json?full=1&perpage=48&q={search_safe}&page=1",
            json=[
                {
                    "id": post_id,
                    "thumbnail": thumb
                }
            ]
        )

        results = api.get_search_results(search)

        assert len(results) == 1
        assert isinstance(results[0], FASubmissionShort)
        assert results[0].submission_id == post_id

    @requests_mock.mock()
    def test_get_search_results_specified_page(self, r):
        post_id = "32342"
        thumb = f"https://t.facdn.net/{post_id}@1600-1562366051.jpg"
        search = "deer"
        api = FAExportAPI("http://example.com/")
        r.get(
            f"http://example.com/search.json?full=1&perpage=48&q={search}&page=2",
            json=[
                {
                    "id": post_id,
                    "thumbnail": thumb
                }
            ]
        )

        results = api.get_search_results(search, 2)

        assert len(results) == 1
        assert isinstance(results[0], FASubmissionShort)
        assert results[0].submission_id == post_id

    @requests_mock.mock()
    def test_get_search_results_no_results(self, r):
        search = "chital_deer"
        api = FAExportAPI("http://example.com/")
        r.get(
            f"http://example.com/search.json?full=1&perpage=48&q={search}&page=1",
            json=[
            ]
        )

        results = api.get_search_results(search)

        assert len(results) == 0
