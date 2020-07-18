import re
from abc import ABC, abstractmethod
from typing import List, Optional

import pytest

from fa_submission import FASubmissionFull, Rating


def _split_text_to_words(text: str) -> List[str]:
    return re.split(r"[\s\"<>]+", text)


class Field(ABC):

    @abstractmethod
    def get_field_words(self, sub: FASubmissionFull) -> List[str]:
        pass

    @abstractmethod
    def get_texts(self, sub: FASubmissionFull) -> List[str]:
        pass

    def __eq__(self, other):
        return isinstance(other, self.__class__)


class KeywordField(Field):

    def get_field_words(self, sub: FASubmissionFull) -> List[str]:
        return sub.keywords

    def get_texts(self, sub: FASubmissionFull) -> List[str]:
        return sub.keywords


class TitleField(Field):

    def get_field_words(self, sub: FASubmissionFull) -> List[str]:
        return _split_text_to_words(sub.title)

    def get_texts(self, sub: FASubmissionFull) -> List[str]:
        return [sub.title]


class DescriptionField(Field):

    def get_field_words(self, sub: FASubmissionFull) -> List[str]:
        return _split_text_to_words(sub.description)

    def get_texts(self, sub: FASubmissionFull) -> List[str]:
        return [sub.description]


class AnyField(Field):
    def get_field_words(self, sub: FASubmissionFull) -> List[str]:
        return _split_text_to_words(sub.title) + \
               _split_text_to_words(sub.description) + \
               sub.keywords

    def get_texts(self, sub: FASubmissionFull) -> List[str]:
        return [sub.title, sub.description] + sub.keywords


class Query(ABC):

    @abstractmethod
    def matches_submission(self, sub: FASubmissionFull):
        pass


class OrQuery(Query):

    def __init__(self, sub_queries: List['Query']):
        self.sub_queries = sub_queries

    def matches_submission(self, sub: FASubmissionFull):
        return any(q.matches_submission(sub) for q in self.sub_queries)

    def __eq__(self, other):
        return (
                isinstance(other, OrQuery)
                and len(self.sub_queries) == len(other.sub_queries)
                and all(self.sub_queries[i] == other.sub_queries[1] for i in range(len(self.sub_queries)))
        )

    def __repr__(self):
        return "OR(" + ", ".join(repr(q) for q in self.sub_queries) + ")"

    def __str__(self):
        return "(" + " OR ".join(str(q) for q in self.sub_queries) + ")"


class AndQuery(Query):

    def __init__(self, sub_queries: List['Query']):
        self.sub_queries = sub_queries

    def matches_submission(self, sub: FASubmissionFull):
        return all(q.matches_submission(sub) for q in self.sub_queries)

    def __eq__(self, other):
        return (
                isinstance(other, AndQuery)
                and len(self.sub_queries) == len(other.sub_queries)
                and all(self.sub_queries[i] == other.sub_queries[i] for i in range(len(self.sub_queries)))
        )

    def __repr__(self):
        return "AND(" + ", ".join(repr(q) for q in self.sub_queries) + ")"

    def __str__(self):
        return "(" + " AND ".join(str(q) for q in self.sub_queries) + ")"


class NotQuery(Query):
    def __init__(self, sub_query: 'Query'):
        self.sub_query = sub_query

    def matches_submission(self, sub: FASubmissionFull):
        return not self.sub_query.matches_submission(sub)

    def __eq__(self, other):
        return isinstance(other, NotQuery) and self.sub_query == other.sub_query

    def __repr__(self):
        return f"NOT({self.sub_query!r})"

    def __str__(self):
        return f"-{self.sub_query}"


class RatingQuery(Query):
    def __init__(self, rating: Rating):
        self.rating = rating

    def matches_submission(self, sub: FASubmissionFull):
        return sub.rating == self.rating

    def __eq__(self, other):
        return isinstance(other, RatingQuery) and self.rating == other.rating

    def __repr__(self):
        return f"RATING({self.rating})"

    def __str__(self):
        return f"rating:{self.rating}"


class WordQuery(Query):

    def __init__(self, word: str, field: Optional['Field'] = None):
        self.word = word
        if field is None:
            field = AnyField()
        self.field = field

    def matches_submission(self, sub: FASubmissionFull):
        return self.word in self.field.get_field_words(sub)

    def __eq__(self, other):
        return isinstance(other, WordQuery) and self.word == other.word and self.field == other.field

    def __repr__(self):
        if self.field == AnyField():
            return f"WORD({self.word})"
        return f"WORD({self.word}, {self.field})"

    def __str__(self):
        if self.field == AnyField():
            return self.word
        return f"{self.field}:{self.word}"


class PrefixQuery(Query):
    def __init__(self, prefix: str, field: Optional['Field'] = None):
        self.prefix = prefix
        if field is None:
            field = AnyField()
        self.field = field

    def matches_submission(self, sub: FASubmissionFull):
        return any(word.startswith(self.prefix) for word in self.field.get_field_words(sub))

    def __eq__(self, other):
        return isinstance(other, PrefixQuery) and self.prefix == other.prefix and self.field == other.field

    def __repr__(self):
        if self.field == AnyField():
            return f"PREFIX({self.prefix})"
        return f"PREFIX({self.prefix}, {self.field})"

    def __str__(self):
        if self.field == AnyField():
            return self.prefix + "*"
        return f"{self.field}:{self.prefix}*"


class SuffixQuery(Query):
    def __init__(self, suffix: str, field: Optional['Field'] = None):
        self.suffix = suffix
        if field is None:
            field = AnyField()
        self.field = field

    def matches_submission(self, sub: FASubmissionFull):
        return any(word.endswith(self.suffix) for word in self.field.get_field_words(sub))

    def __eq__(self, other):
        return isinstance(other, SuffixQuery) and self.suffix == other.suffix and self.field == other.field

    def __repr__(self):
        if self.field == AnyField():
            return f"SUFFIX({self.suffix})"
        return f"SUFFIX({self.suffix}, {self.field})"

    def __str__(self):
        if self.field == AnyField():
            return "*" + self.suffix
        return f"{self.field}:*{self.suffix}"


class RegexQuery(Query):
    def __init__(self, regex: str, field: Optional['Field'] = None):
        self.regex = regex
        if field is None:
            field = AnyField()
        self.field = field

    def matches_submission(self, sub: FASubmissionFull):
        return any(re.search(self.regex, word) for word in self.field.get_field_words(sub))

    def __eq__(self, other):
        return isinstance(other, RegexQuery) and self.regex == other.regex and self.field == other.field

    def __repr__(self):
        if self.field == AnyField():
            return f"REGEX({self.regex})"
        return f"REGEX({self.regex}, {self.field})"

    def __str__(self):
        if self.field == AnyField():
            return self.regex
        return f"{self.field}:{self.regex}"


class PhraseQuery(Query):
    def __init__(self, phrase: str, field: Optional['Field'] = None):
        self.phrase = phrase
        if field is None:
            field = AnyField()
        self.field = field

    def matches_submission(self, sub: FASubmissionFull):
        return any(self.phrase in text for text in self.field.get_texts(sub))

    def __eq__(self, other):
        return isinstance(other, PhraseQuery) and self.phrase == other.phrase and self.field == other.field

    def __repr__(self):
        if self.field == AnyField():
            return f"PHRASE({self.phrase})"
        return f"PHRASE(\"{self.phrase}\", {self.field})"

    def __str__(self):
        if self.field == AnyField():
            return f"\"{self.phrase}\""
        return f"{self.field}:\"{self.phrase}\""


def get_field_for_name(name: str) -> 'Field':
    return {
        "title": TitleField(),
        "description": DescriptionField(),
        "keywords": KeywordField()
    }[name]


class InvalidQueryException(Exception):
    pass


def query_parser(query_str: str) -> 'Query':
    # Handle quotes
    # Handle brackets
    # Handle field names
    # Handle and/or
    split_query = query_str.split()
    if len(split_query) > 1:
        return AndQuery([query_parser(word) for word in split_query])
    # Handle not
    if query_str.startswith("!") or query_str.startswith("-"):
        return NotQuery(query_parser(query_str[1:]))
    # Handle words & wildcards
    return WordQuery(query_str)


def test_parser():
    assert query_parser("first") == WordQuery("first")
    assert query_parser("first document") == AndQuery([WordQuery("first"), WordQuery("document")])
    assert query_parser("-first") == NotQuery(WordQuery("first"))
    assert query_parser("!first") == NotQuery(WordQuery("first"))
    assert query_parser("! first") == NotQuery(WordQuery("first"))
    assert query_parser("not first") == NotQuery(WordQuery("first"))
    assert query_parser("first and document") == AndQuery([WordQuery("first"), WordQuery("document")])
    assert query_parser("first or document") == OrQuery([WordQuery("first"), WordQuery("document")])
    assert query_parser("first and (doc or document)") == AndQuery(
        [WordQuery("first"), OrQuery([WordQuery("doc"), WordQuery("document")])])
    assert query_parser("first (doc or document)") == AndQuery(
        [WordQuery("first"), OrQuery([WordQuery("doc"), WordQuery("document")])])
    with pytest.raises(InvalidQueryException):
        query_parser("first (doc or document")
    assert query_parser("\"first document\"") == PhraseQuery("first document")
    assert query_parser("keyword:first document") == AndQuery(
        [WordQuery("first", KeywordField()), WordQuery("document")])
    assert query_parser("keyword:\"first document\"") == PhraseQuery("first document", KeywordField())
    assert query_parser("keyword:(first and document)") == AndQuery(
        [WordQuery("first", KeywordField()), WordQuery("document"), KeywordField()])
    assert query_parser("@keyword first document") == AndQuery(
        [WordQuery("first", KeywordField()), WordQuery("document")])
    assert query_parser("title:first") == WordQuery("first", TitleField())
    assert query_parser("description:first") == WordQuery("first", DescriptionField())
    assert query_parser("first*") == PrefixQuery("first")
    assert query_parser("*first") == SuffixQuery("first")
    assert query_parser("fi*st") == RegexQuery("fi.*st")
    assert query_parser("fi[*st") == RegexQuery(r"fi\[.*st")
    assert query_parser("not (hello \"first :) document\")") == NotQuery(
        AndQuery([WordQuery("hello"), PhraseQuery("first :) document")]))
    with pytest.raises(InvalidQueryException):
        query_parser("\"hello \" document\"")
    assert query_parser("\"hello \\\" document\"") == PhraseQuery("hello \" document")
