import datetime
import unittest

from subscription_watcher import Subscription
from tests.util.submission_builder import SubmissionBuilder


class SubscriptionTest(unittest.TestCase):

    def test_init(self):
        query = "yo"
        destination = 12432

        sub = Subscription(query, destination)

        assert sub.query == query
        assert sub.destination == destination
        assert sub.latest_update is None

    def test_matches_result__one_word_in_title_matches(self):
        query = "test"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_result__one_word_in_description_matches(self):
        query = "this"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_result__one_word_in_keywords_matches(self):
        query = "keywords"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_result__substring_in_title_no_match(self):
        query = "test"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="testing submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert not match

    def test_matches_result__substring_in_description_no_match(self):
        query = "his"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert not match

    def test_matches_result__substring_in_keywords_no_match(self):
        query = "keyword"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert not match

    def test_matches_result__one_word_no_match(self):
        query = "query"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert not match

    def test_matches_result__two_words_in_title_matches(self):
        query = "submission test"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test submission",
            description="this is just an example",
            keywords=["example", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_result__two_words_in_description_matches(self):
        query = "example submission"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test",
            description="this submission is just an example",
            keywords=["example", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_result__two_matching_keywords(self):
        query = "submission keywords"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test",
            description="this is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_result__two_words_in_title_and_description_matches(self):
        query = "test this"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_result__two_words_in_title_and_keyword_matches(self):
        query = "test keywords"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_result__two_words_one_matches(self):
        query = "query"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert not match

    def test_matches_result__case_insensitive_title(self):
        query = "test"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="Test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_result__case_insensitive_description(self):
        query = "this"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test submission",
            description="This submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_result__case_insensitive_keywords(self):
        query = "keywords"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "KEYWORDS"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_result__case_insensitive_query(self):
        query = "SUBMISSION"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_result__does_not_match_negated_query(self):
        query = "-test"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert not match

    def test_matches_result__does_not_match_negated_query_case_insensitive(self):
        query = "-test"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="Test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert not match

    def test_matches_result__matches_non_applicable_negated_query(self):
        query = "-deer"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="Test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_result__matches_query_with_non_applicable_negated_query(self):
        query = "test -deer"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="Test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_result__does_not_match_query_with_applicable_negated_query(self):
        query = "test -example"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="Test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert not match

    def test_matches_result__does_not_match_query_with_applicable_negated_query_in_same_text(self):
        query = "this -example"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="Test submission",
            description="this submission is just an example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert not match

    def test_matches_result__matches_query_with_hyphen(self):
        query = "an-example"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="Test submission",
            description="this submission is just an-example",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_word_in_quotes(self):
        query = "deer"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="Test submission",
            description="this submission is=\"deer\"",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_matches_word_in_tag(self):
        query = "deer"
        subscription = Subscription(query, 12432)
        submission = SubmissionBuilder(
            title="Test submission",
            description="this submission is <b>deer</b>",
            keywords=["example", "submission", "keywords"]
        ).build_full_submission()

        match = subscription.matches_result(submission)

        assert match

    def test_to_json_no_updates(self):
        sub = Subscription("test query", -12322)

        data = sub.to_json()
        assert "query" in data
        assert data["query"] == "test query"
        assert "destination" in data
        assert data["destination"] == -12322
        assert "latest_update" in data
        assert data["latest_update"] is None

    def test_to_json(self):
        sub = Subscription("test query", -12322)
        sub.latest_update = datetime.datetime(2019, 9, 17, 21, 8, 35)

        data = sub.to_json()
        assert "query" in data
        assert data["query"] == "test query"
        assert "destination" in data
        assert data["destination"] == -12322
        assert "latest_update" in data
        assert data["latest_update"] == "2019-09-17T21:08:35"

    def test_from_json_no_update(self):
        data = {
            "query": "example query",
            "destination": 17839,
            "latest_update": None
        }

        sub = Subscription.from_json(data)
        assert sub.query == "example query"
        assert sub.destination == 17839
        assert sub.latest_update is None

    def test_from_json(self):
        data = {
            "query": "example query",
            "destination": 17839,
            "latest_update": "2019-09-17T21:14:07Z"
        }

        sub = Subscription.from_json(data)
        assert sub.query == "example query"
        assert sub.destination == 17839
        assert sub.latest_update == datetime.datetime(2019, 9, 17, 21, 14, 7, tzinfo=datetime.timezone.utc)

    def test_to_json_and_back_no_update(self):
        sub = Subscription("an example", -63939)

        data = sub.to_json()
        new_sub = Subscription.from_json(data)

        assert new_sub.query == sub.query
        assert new_sub.destination == sub.destination
        assert new_sub.latest_update == sub.latest_update

    def test_to_json_and_back(self):
        sub = Subscription("something", 3223)
        sub.latest_update = datetime.datetime(2019, 9, 17, 21, 16, 14, tzinfo=datetime.timezone.utc)

        data = sub.to_json()
        new_sub = Subscription.from_json(data)

        assert new_sub.query == sub.query
        assert new_sub.destination == sub.destination
        assert new_sub.latest_update == sub.latest_update
