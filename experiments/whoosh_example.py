from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import List

from whoosh.fields import *
from whoosh.filedb.filestore import RamStorage
from whoosh.qparser import MultifieldParser
from whoosh.query import Query, Or, Term, Prefix, Wildcard, And, Phrase
from whoosh.searching import Searcher

from fa_submission import FASubmissionFull, Rating, FAUser
from subscription_watcher import Subscription, rating_dict

schema = Schema(title=TEXT, description=TEXT, keywords=KEYWORD)
search_fields = ["title", "description", "keywords"]


def matches_subscription(sub: FASubmissionFull, q: Query) -> bool:
    with RamStorage() as store:
        ix = store.create_index(schema)
        writer = ix.writer()
        writer.add_document(
            title=sub.title,
            description=sub.description,
            keywords=sub.keywords
        )
        writer.commit()
        with ix.searcher() as searcher:
            results = searcher.search(q)
            return bool(results)


@contextmanager
def single_doc_index(sub: FASubmissionFull):
    with RamStorage() as store:
        ix = store.create_index(schema)
        writer = ix.writer()
        writer.add_document(
            title=sub.title,
            description=sub.description,
            keywords=sub.keywords
        )
        writer.commit()
        with ix.searcher() as searcher:
            yield searcher


def match_search_query(searcher: Searcher, q: Query) -> bool:
    return bool(searcher.search(q))


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


def whoosh_to_custom(q: Query) -> 'Query':
    if isinstance(q, Or):
        return OrQuery([whoosh_to_custom(w) for w in q.subqueries])
    if isinstance(q, And):
        return AndQuery([whoosh_to_custom(w) for w in q.subqueries])
    if isinstance(q, Term):
        if q.fieldname == "rating":
            return RatingQuery(rating_dict[q.text])
        field = get_field_for_name(q.fieldname)
        return TextQuery(q.text, field)
    if isinstance(q, Prefix):
        field = get_field_for_name(q.fieldname)
        return PrefixQuery(q.text, field)
    if isinstance(q, Wildcard):
        field = get_field_for_name(q.fieldname)
        regex = fnmatch.translate(q.text)
        return RegexQuery(regex, field)
    if isinstance(q, Phrase):
        field = get_field_for_name(q.fieldname)
        quote = " ".join(q.words)
        return PhraseQuery(quote, field)
    raise NotImplementedError


if __name__ == "__main__":
    sub1 = FASubmissionFull(
        "123",
        "thumb1.png",
        "image1.png",
        "image1.png",
        "First document",
        FAUser("uploader", "uploader"),
        "This is the first document we've added!",
        ["first", "document"],
        Rating.GENERAL
    )
    sub2 = FASubmissionFull(
        "234",
        "thumb2.png",
        "image1.png",
        "image1.png",
        "Second document",
        FAUser("uploader", "uploader"),
        "The second one is even more interesting!",
        ["second", "document"],
        Rating.GENERAL
    )

    print("Whoosh time:")
    query = MultifieldParser(search_fields, schema).parse("first")
    start_time = datetime.datetime.now()
    for _ in range(50):
        assert matches_subscription(sub1, query)
        assert not matches_subscription(sub2, query)
    end_time = datetime.datetime.now()
    print((end_time - start_time) / 100)
    print(((end_time - start_time) / 100).microseconds)

    print("Whoosh reuse index time:")
    query1 = MultifieldParser(search_fields, schema).parse("first")
    query2 = MultifieldParser(search_fields, schema).parse("second")
    start_time = datetime.datetime.now()
    with single_doc_index(sub1) as searcher:
        sub_start_time = datetime.datetime.now()
        for _ in range(50):
            assert match_search_query(searcher, query1)
            assert not match_search_query(searcher, query2)
        sub_end_time = datetime.datetime.now()
    end_time = datetime.datetime.now()
    print((end_time - start_time) / 100)
    print(((end_time - start_time) / 100).microseconds)
    print("  (Without searcher setup):")
    print((sub_end_time - sub_start_time) / 100)
    print(((sub_end_time - sub_start_time) / 100).microseconds)

    print("Whoosh to custom time:")
    query = MultifieldParser(search_fields, schema).parse("first")
    custom_query = whoosh_to_custom(query)
    start_time = datetime.datetime.now()
    for _ in range(50):
        assert custom_query.matches_submission(sub1)
        assert not custom_query.matches_submission(sub2)
    end_time = datetime.datetime.now()
    print((end_time - start_time) / 100)
    print(((end_time - start_time) / 100).microseconds)

    print("Current code time:")
    start_time = datetime.datetime.now()
    subscription = Subscription("first", 0)
    for _ in range(50):
        assert subscription.matches_result(sub1, set())
        assert not subscription.matches_result(sub2, set())
    end_time = datetime.datetime.now()
    print((end_time - start_time) / 100)
    print(((end_time - start_time) / 100).microseconds)
