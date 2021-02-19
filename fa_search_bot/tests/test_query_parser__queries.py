from fa_search_bot.fa_submission import Rating, FAUser
from fa_search_bot.query_parser import MatchLocation, FieldLocation, RatingQuery, WordQuery, TitleField, \
    DescriptionField, KeywordField, ArtistField
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder


def test_match_location_overlaps():
    location1 = MatchLocation(FieldLocation("title"), 0, 5)
    location2 = MatchLocation(FieldLocation("title"), 4, 8)

    assert location1.overlaps(location2)


def test_match_location_overlaps__tips_touch():
    location1 = MatchLocation(FieldLocation("title"), 0, 5)
    location2 = MatchLocation(FieldLocation("title"), 5, 8)

    assert not location1.overlaps(location2)


def test_match_location_overlaps__no_touch():
    location1 = MatchLocation(FieldLocation("title"), 0, 5)
    location2 = MatchLocation(FieldLocation("title"), 6, 8)

    assert not location1.overlaps(location2)


def test_match_location_overlaps__different_field():
    location1 = MatchLocation(FieldLocation("title"), 0, 5)
    location2 = MatchLocation(FieldLocation("description"), 4, 8)

    assert not location1.overlaps(location2)


def test_match_location_overlaps__one_envelopes_two():
    location1 = MatchLocation(FieldLocation("title"), 0, 10)
    location2 = MatchLocation(FieldLocation("title"), 4, 8)

    assert location1.overlaps(location2)


def test_match_location_overlaps__two_envelopes_one():
    location1 = MatchLocation(FieldLocation("title"), 6, 7)
    location2 = MatchLocation(FieldLocation("title"), 4, 8)

    assert location1.overlaps(location2)


def test_match_location_overlaps_any():
    location1 = MatchLocation(FieldLocation("title"), 0, 6)
    location2 = MatchLocation(FieldLocation("title"), 4, 8)
    location3 = MatchLocation(FieldLocation("description"), 4, 8)

    assert location1.overlaps_any([location2, location3])


def test_match_location_overlaps_any__overlaps_all():
    location1 = MatchLocation(FieldLocation("title"), 0, 6)
    location2 = MatchLocation(FieldLocation("title"), 0, 4)
    location3 = MatchLocation(FieldLocation("title"), 5, 8)

    assert location1.overlaps_any([location2, location3])


def test_match_location_overlaps_any__overlaps_none():
    location1 = MatchLocation(FieldLocation("title"), 0, 4)
    location2 = MatchLocation(FieldLocation("title"), 5, 8)
    location3 = MatchLocation(FieldLocation("title"), 10, 15)

    assert not location1.overlaps_any([location2, location3])


def test_match_location_overlaps_any__overlaps_only_in_other_fields():
    location1 = MatchLocation(FieldLocation("title"), 0, 6)
    location2 = MatchLocation(FieldLocation("description"), 0, 4)
    location3 = MatchLocation(FieldLocation("description"), 5, 8)

    assert not location1.overlaps_any([location2, location3])


def test_or_query():
    assert False
    pass


def test_location_or_query():
    assert False
    pass


def test_any_query():
    assert False
    pass


def test_not_query():
    assert False
    pass


def test_rating_query():
    submission = SubmissionBuilder(rating=Rating.GENERAL).build_full_submission()
    query = RatingQuery(Rating.GENERAL)

    assert query.matches_submission(submission)


def test_rating_query__no_match():
    submission = SubmissionBuilder(rating=Rating.MATURE).build_full_submission()
    query = RatingQuery(Rating.GENERAL)

    assert not query.matches_submission(submission)


def test_word_query__title():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "example"]
    ).build_full_submission()
    query = WordQuery("test")

    assert query.matches_submission(submission)


def test_word_query__description():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "example"]
    ).build_full_submission()
    query = WordQuery("hello")

    assert query.matches_submission(submission)


def test_word_query__keywords():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "example"]
    ).build_full_submission()
    query = WordQuery("query")

    assert query.matches_submission(submission)


def test_word_query__no_match():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "example"]
    ).build_full_submission()
    query = WordQuery("testing")

    assert not query.matches_submission(submission)


def test_word_query__all_fields():
    submission = SubmissionBuilder(
        title="test",
        description="hello test world",
        keywords=["query", "example", "test"]
    ).build_full_submission()
    query = WordQuery("test")

    assert query.matches_submission(submission)


def test_word_query__punctuation_title():
    submission = SubmissionBuilder(
        title="test!",
        description="hello world",
        keywords=["query", "example"]
    ).build_full_submission()
    query = WordQuery("test")

    assert query.matches_submission(submission)


def test_word_query__punctuation_description():
    submission = SubmissionBuilder(
        title="test",
        description="hello, world",
        keywords=["query", "example"]
    ).build_full_submission()
    query = WordQuery("hello")

    assert query.matches_submission(submission)


def test_word_query__not_artist():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "example"],
        author=FAUser("Testing", "testing")
    ).build_full_submission()
    query = WordQuery("testing")

    assert not query.matches_submission(submission)


def test_word_query__keyword_non_concat():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["test", "thing"]
    ).build_full_submission()
    query = WordQuery("testthing")

    assert not query.matches_submission(submission)


def test_word_query__keyword_punctuation():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["test", "thing!"]
    ).build_full_submission()
    query = WordQuery("thing")

    assert query.matches_submission(submission)


def test_word_query__hyphenated_match():
    submission = SubmissionBuilder(
        title="test",
        description="hello-world",
        keywords=["test", "thing"]
    ).build_full_submission()
    query = WordQuery("hello-world")

    assert query.matches_submission(submission)


def test_word_query__hyphenated_no_match_part():
    submission = SubmissionBuilder(
        title="test",
        description="hello-world",
        keywords=["test", "thing"]
    ).build_full_submission()
    query = WordQuery("hello")

    assert not query.matches_submission(submission)


def test_word_query__not_word_part():
    submission = SubmissionBuilder(
        title="test",
        description="hello-world",
        keywords=["testing", "things"]
    ).build_full_submission()
    query = WordQuery("thing")

    assert not query.matches_submission(submission)


def test_word_query__title_field():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "thing"]
    ).build_full_submission()
    query = WordQuery("test", TitleField())

    assert query.matches_submission(submission)


def test_word_query__title_field_no_match():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "thing"]
    ).build_full_submission()
    query = WordQuery("hello", TitleField())

    assert not query.matches_submission(submission)


def test_word_query__description_field():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "thing"]
    ).build_full_submission()
    query = WordQuery("hello", DescriptionField())

    assert query.matches_submission(submission)


def test_word_query__description_field_no_match():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "thing"]
    ).build_full_submission()
    query = WordQuery("test", DescriptionField())

    assert not query.matches_submission(submission)


def test_word_query__keyword_field():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "thing"]
    ).build_full_submission()
    query = WordQuery("query", KeywordField())

    assert query.matches_submission(submission)


def test_word_query__keyword_field_no_match():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "thing"]
    ).build_full_submission()
    query = WordQuery("hello", KeywordField())

    assert not query.matches_submission(submission)


def test_word_query__artist_field():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "thing"],
        author=FAUser("TestAccount", "testaccount")
    ).build_full_submission()
    query = WordQuery("testaccount", ArtistField())

    assert query.matches_submission(submission)


def test_word_query__artist_field_no_match():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "thing"],
        author=FAUser("Abe_E_Seedy", "abeeseedy")
    ).build_full_submission()
    query = WordQuery("hello", ArtistField())

    assert not query.matches_submission(submission)


def test_word_query__artist_field_full_name():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "thing"],
        author=FAUser("Abe_E_Seedy", "abeeseedy")
    ).build_full_submission()
    query = WordQuery("Abe_E_Seedy", ArtistField())

    assert query.matches_submission(submission)


def test_word_query__artist_field_punctuation():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "thing"],
        author=FAUser("-Sebastian-", "-sebastian-")
    ).build_full_submission()
    query = WordQuery("-sebastian-", ArtistField())

    assert query.matches_submission(submission)


def test_word_query__locations_title():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "thing"]
    ).build_full_submission()
    query = WordQuery("test")

    locations = query.match_locations(submission)

    assert len(locations) == 1
    assert locations[0].field == FieldLocation("title")
    assert locations[0].start_position == 0
    assert locations[0].end_position == 4


def test_word_query__locations_description():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "thing"]
    ).build_full_submission()
    query = WordQuery("world")

    locations = query.match_locations(submission)

    assert len(locations) == 1
    assert locations[0].field == FieldLocation("description")
    assert locations[0].start_position == 6
    assert locations[0].end_position == 11


def test_word_query__locations_keywords():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "thing"]
    ).build_full_submission()
    query = WordQuery("thing")

    locations = query.match_locations(submission)

    assert len(locations) == 1
    assert locations[0].field == FieldLocation("keyword_1")
    assert locations[0].start_position == 0
    assert locations[0].end_position == 5


def test_word_query__locations_multiple():
    submission = SubmissionBuilder(
        title="test",
        description="hello test",
        keywords=["query", "test"]
    ).build_full_submission()
    query = WordQuery("test")

    locations = query.match_locations(submission)

    assert len(locations) == 3
    assert MatchLocation(FieldLocation("title"), 0, 4) in locations
    assert MatchLocation(FieldLocation("description"), 6, 10) in locations
    assert MatchLocation(FieldLocation("keyword_1"), 0, 4) in locations


def test_word_query__locations_none():
    submission = SubmissionBuilder(
        title="test",
        description="hello world",
        keywords=["query", "word"]
    ).build_full_submission()
    query = WordQuery("fred")

    locations = query.match_locations(submission)

    assert len(locations) == 0


def test_word_query__locations_no_match_hypenated():
    submission = SubmissionBuilder(
        title="test",
        description="hello-world",
        keywords=["test", "thing"]
    ).build_full_submission()
    query = WordQuery("hello")

    locations = query.match_locations(submission)

    assert len(locations) == 0


def test_prefix_query():
    assert False
    pass


def test_suffix_query():
    assert False
    pass


def test_regex_query():
    assert False
    pass


def test_phrase_query():
    assert False
    pass


def test_exception_query():
    assert False
    pass
