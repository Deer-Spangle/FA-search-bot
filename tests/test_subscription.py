import datetime

from subscription_watcher import Subscription
from tests.util.submission_builder import SubmissionBuilder


def test_init():
    query = "yo"
    destination = 12432

    sub = Subscription(query, destination)

    assert sub.query == query
    assert sub.destination == destination
    assert sub.latest_update is None


def test_matches_result__one_word_in_title_matches():
    query = "test"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_result__one_word_in_description_matches():
    query = "this"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_result__one_word_in_keywords_matches():
    query = "keywords"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_result__substring_in_title_no_match():
    query = "test"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="testing submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert not match


def test_matches_result__substring_in_description_no_match():
    query = "his"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert not match


def test_matches_result__substring_in_keywords_no_match():
    query = "keyword"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert not match


def test_matches_result__one_word_no_match():
    query = "query"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert not match


def test_matches_result__two_words_in_title_matches():
    query = "submission test"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test submission",
        description="this is just an example",
        keywords=["example", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_result__two_words_in_description_matches():
    query = "example submission"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test",
        description="this submission is just an example",
        keywords=["example", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_result__two_matching_keywords():
    query = "submission keywords"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test",
        description="this is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_result__two_words_in_title_and_description_matches():
    query = "test this"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_result__two_words_in_title_and_keyword_matches():
    query = "test keywords"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_result__two_words_one_matches():
    query = "query"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert not match


def test_matches_result__case_insensitive_title():
    query = "test"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="Test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_result__case_insensitive_description():
    query = "this"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test submission",
        description="This submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_result__case_insensitive_keywords():
    query = "keywords"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "KEYWORDS"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_result__case_insensitive_query():
    query = "SUBMISSION"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_result__does_not_match_negated_query():
    query = "-test"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert not match


def test_matches_result__does_not_match_negated_query_case_insensitive():
    query = "-test"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="Test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert not match


def test_matches_result__matches_non_applicable_negated_query():
    query = "-deer"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="Test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_result__matches_query_with_non_applicable_negated_query():
    query = "test -deer"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="Test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_result__does_not_match_query_with_applicable_negated_query():
    query = "test -example"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="Test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert not match


def test_matches_result__does_not_match_query_with_applicable_negated_query_in_same_text():
    query = "this -example"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="Test submission",
        description="this submission is just an example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert not match


def test_matches_result__matches_query_with_hyphen():
    query = "an-example"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="Test submission",
        description="this submission is just an-example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_result__doesnt_match_blacklisted_tag():
    query = "an-example"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="Test submission",
        description="this submission is just an-example",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, {"test"})

    assert not match


def test_matches_word_in_quotes():
    query = "deer"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="Test submission",
        description="this submission is=\"deer\"",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_matches_word_in_tag():
    query = "deer"
    subscription = Subscription(query, 12432)
    submission = SubmissionBuilder(
        title="Test submission",
        description="this submission is <b>deer</b>",
        keywords=["example", "submission", "keywords"]
    ).build_full_submission()

    match = subscription.matches_result(submission, set())

    assert match


def test_to_json_no_updates():
    sub = Subscription("test query", -12322)

    data = sub.to_json()
    assert "query" in data
    assert data["query"] == "test query"
    assert "destination" in data
    assert data["destination"] == -12322
    assert "latest_update" in data
    assert data["latest_update"] is None


def test_to_json():
    sub = Subscription("test query", -12322)
    sub.latest_update = datetime.datetime(2019, 9, 17, 21, 8, 35)

    data = sub.to_json()
    assert "query" in data
    assert data["query"] == "test query"
    assert "destination" in data
    assert data["destination"] == -12322
    assert "latest_update" in data
    assert data["latest_update"] == "2019-09-17T21:08:35"


def test_from_json_no_update():
    data = {
        "query": "example query",
        "destination": 17839,
        "latest_update": None
    }

    sub = Subscription.from_json(data)
    assert sub.query == "example query"
    assert sub.destination == 17839
    assert sub.latest_update is None


def test_from_json():
    data = {
        "query": "example query",
        "destination": 17839,
        "latest_update": "2019-09-17T21:14:07Z"
    }

    sub = Subscription.from_json(data)
    assert sub.query == "example query"
    assert sub.destination == 17839
    assert sub.latest_update == datetime.datetime(2019, 9, 17, 21, 14, 7, tzinfo=datetime.timezone.utc)


def test_to_json_and_back_no_update():
    sub = Subscription("an example", -63939)

    data = sub.to_json()
    new_sub = Subscription.from_json(data)

    assert new_sub.query == sub.query
    assert new_sub.destination == sub.destination
    assert new_sub.latest_update == sub.latest_update


def test_to_json_and_back():
    sub = Subscription("something", 3223)
    sub.latest_update = datetime.datetime(2019, 9, 17, 21, 16, 14, tzinfo=datetime.timezone.utc)

    data = sub.to_json()
    new_sub = Subscription.from_json(data)

    assert new_sub.query == sub.query
    assert new_sub.destination == sub.destination
    assert new_sub.latest_update == sub.latest_update
