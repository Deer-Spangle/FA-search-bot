from abc import ABC
from contextlib import contextmanager
from typing import List

from whoosh.fields import *
from whoosh.filedb.filestore import RamStorage
from whoosh.qparser import MultifieldParser
from whoosh.query import Query, Or, Term
from whoosh.searching import Searcher

from fa_submission import FASubmissionFull, Rating, FAUser
from subscription_watcher import Subscription

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


class WordQuery(Query):
    def __init__(self, word):
        self.word = word

    def matches_submission(self, sub: FASubmissionFull):
        all_text = \
            re.split(r"[\s\"<>]+", sub.title) + \
            re.split(r"[\s\"<>]+", sub.description) + \
            sub.keywords
        return self.word in all_text


class NotQuery(Query):
    def __init__(self, sub_query: 'Query'):
        self.sub_query = sub_query

    def matches_submission(self, sub: FASubmissionFull):
        return not self.sub_query.matches_submission(sub)


class FieldQuery(Query):
    def __init__(self, field: str, term: str):
        self.field = field
        self.term = term

    def matches_submission(self, sub: FASubmissionFull):
        print("ERRR")
        raise NotImplementedError


class RatingQuery(Query):
    def __init__(self, rating: Rating):
        self.rating = rating

    def matches_submission(self, sub: FASubmissionFull):
        return sub.rating == self.rating


class KeywordQuery(Query):
    def __init__(self, keyword: str):
        self.keyword = keyword

    def matches_submission(self, sub: FASubmissionFull):
        return self.keyword in sub.keywords


class TitleQuery(Query):
    def __init__(self, word):
        self.word = word

    def matches_submission(self, sub: FASubmissionFull):
        return self.word in re.split(r"[\s\"<>]+", sub.title)


class DescriptionQuery(Query):
    def __init__(self, word):
        self.word = word

    def matches_submission(self, sub: FASubmissionFull):
        return self.word in re.split(r"[\s\"<>]+", sub.description)


def whoosh_to_custom(q: Query) -> 'Query':
    if isinstance(q, Or):
        return OrQuery([whoosh_to_custom(w) for w in q.subqueries])
    if isinstance(q, Term):
        if q.fieldname == "title":
            return TitleQuery(q.text)
        if q.fieldname == "description":
            return DescriptionQuery(q.text)
        if q.fieldname == "keywords":
            return KeywordQuery(q.text)
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
