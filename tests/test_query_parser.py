import pytest

from fa_submission import Rating
from query_parser import parse_query, WordQuery, AndQuery, NotQuery, OrQuery, KeywordField, InvalidQueryException, \
    PhraseQuery, TitleField, RatingQuery, DescriptionField, PrefixQuery, SuffixQuery, RegexQuery


def test_parser():
    assert parse_query("first") == WordQuery("first")
    assert parse_query("first document") == AndQuery([WordQuery("first"), WordQuery("document")])
    assert parse_query("-first") == NotQuery(WordQuery("first"))
    assert parse_query("!first") == NotQuery(WordQuery("first"))
    assert parse_query("! first") == NotQuery(WordQuery("first"))
    assert parse_query("not first") == NotQuery(WordQuery("first"))
    assert parse_query("NOT first") == NotQuery(WordQuery("first"))
    assert parse_query("first and document") == AndQuery([WordQuery("first"), WordQuery("document")])
    assert parse_query("first or document") == OrQuery([WordQuery("first"), WordQuery("document")])
    assert parse_query("first AND doc OR document") == OrQuery(
        [AndQuery([WordQuery("first"), WordQuery("doc")]), WordQuery("document")]
    )
    assert parse_query("(first)") == WordQuery("first")
    assert parse_query("first and (doc or document)") == AndQuery(
        [WordQuery("first"), OrQuery([WordQuery("doc"), WordQuery("document")])]
    )
    assert parse_query("first (doc or document)") == AndQuery(
        [WordQuery("first"), OrQuery([WordQuery("doc"), WordQuery("document")])]
    )
    with pytest.raises(InvalidQueryException):
        parse_query("first (doc or document")
    assert parse_query("\"first document\"") == PhraseQuery("first document")
    assert parse_query("keyword:first document") == AndQuery(
        [WordQuery("first", KeywordField()), WordQuery("document")]
    )
    assert parse_query("keyword:\"first document\"") == PhraseQuery("first document", KeywordField())
    with pytest.raises(InvalidQueryException):
        parse_query("keyword:(first and document)")
    assert parse_query("@keyword first document") == AndQuery(
        [WordQuery("first", KeywordField()), WordQuery("document")]
    )
    assert parse_query("title:first") == WordQuery("first", TitleField())
    assert parse_query("TITLE: first") == WordQuery("first", TitleField())
    assert parse_query("description:first") == WordQuery("first", DescriptionField())
    assert parse_query("rating:general") == RatingQuery(Rating.GENERAL)
    with pytest.raises(InvalidQueryException):
        parse_query("fake:first")
    assert parse_query("first*") == PrefixQuery("first")
    assert parse_query("*first") == SuffixQuery("first")
    assert parse_query("fi*st") == RegexQuery("fi.*st")
    assert parse_query("fi[*st") == RegexQuery(r"fi\[.*st")
    assert parse_query("\"Hello WORLD!\"") == PhraseQuery("Hello WORLD!")
    assert parse_query("not (hello \"first :) document\")") == NotQuery(
        AndQuery([WordQuery("hello"), PhraseQuery("first :) document")])
    )
    with pytest.raises(InvalidQueryException):
        parse_query("\"hello \" document\"")
    assert parse_query("\"hello \\\" document\"") == PhraseQuery("hello \" document")
