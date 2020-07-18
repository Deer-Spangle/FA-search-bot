import re
from abc import ABC, abstractmethod
from typing import List

from fa_submission import FASubmissionFull, Rating


class Query(ABC):

    @abstractmethod
    def matches_submission(self, sub: FASubmissionFull):
        pass


class OrQuery(Query):

    def __init__(self, sub_queries: List['Query']):
        self.sub_queries = sub_queries

    def matches_submission(self, sub: FASubmissionFull):
        return any(q.matches_submission(sub) for q in self.sub_queries)


class AndQuery(Query):

    def __init__(self, sub_queries: List['Query']):
        self.sub_queries = sub_queries

    def matches_submission(self, sub: FASubmissionFull):
        return all(q.matches_submission(sub) for q in self.sub_queries)


class NotQuery(Query):
    def __init__(self, sub_query: 'Query'):
        self.sub_query = sub_query

    def matches_submission(self, sub: FASubmissionFull):
        return not self.sub_query.matches_submission(sub)


class RatingQuery(Query):
    def __init__(self, rating: Rating):
        self.rating = rating

    def matches_submission(self, sub: FASubmissionFull):
        return sub.rating == self.rating


class TextQuery(Query):

    def __init__(self, word: str, field: 'Field'):
        self.word = word
        self.field = field

    def matches_submission(self, sub: FASubmissionFull):
        return self.word in self.field.get_field_words(sub)


def _split_text_to_words(text: str) -> List[str]:
    return re.split(r"[\s\"<>]+", text)


class Field(ABC):

    @abstractmethod
    def get_field_words(self, sub: FASubmissionFull) -> List[str]:
        pass

    @abstractmethod
    def get_texts(self, sub: FASubmissionFull) -> List[str]:
        pass


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


class PrefixQuery(Query):
    def __init__(self, prefix: str, field: Field):
        self.prefix = prefix
        self.field = field

    def matches_submission(self, sub: FASubmissionFull):
        return any(word.startswith(self.prefix) for word in self.field.get_field_words(sub))


class RegexQuery(Query):
    def __init__(self, regex: str, field: Field):
        self.regex = regex
        self.field = field

    def matches_submission(self, sub: FASubmissionFull):
        return any(re.search(self.regex, word) for word in self.field.get_field_words(sub))


class PhraseQuery(Query):
    def __init__(self, phrase: str, field: Field):
        self.phrase = phrase
        self.field = field

    def matches_submission(self, sub: FASubmissionFull):
        return any(self.phrase in text for text in self.field.get_texts(sub))


def get_field_for_name(name: str) -> 'Field':
    return {
        "title": TitleField(),
        "description": DescriptionField(),
        "keywords": KeywordField()
    }[name]


def query_parser(query_str: str) -> 'Query':
    pass


def test_parser():
    pass
