import unittest

import requests_mock

from fa_export_api import FAExportAPI, PageNotFound
from fa_submission import FASubmissionFull


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






"""
- Get user folder returns list of short submission objects
- Get user folder works with scraps
- Get user folder works with awkward usernames (l[i]s)
- Get user folder works with specified page
- Get user folder handles empty folder
- Get search results works
- Get search results handles combination query modifiers &|!-
- Get search results pages correctly
- Get search results handles empty folder
"""