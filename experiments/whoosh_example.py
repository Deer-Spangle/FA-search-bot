from contextlib import contextmanager

from whoosh.fields import *
from whoosh.filedb.filestore import RamStorage
from whoosh.qparser import MultifieldParser
from whoosh.query import Query
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
    print((end_time-start_time)/100)
    print(((end_time-start_time)/100).microseconds)

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
    print((end_time-start_time)/100)
    print(((end_time-start_time)/100).microseconds)
    print("  (Without searcher setup):")
    print((sub_end_time-sub_start_time)/100)
    print(((sub_end_time-sub_start_time)/100).microseconds)

    print("Current code time:")
    start_time = datetime.datetime.now()
    subscription = Subscription("first", 0)
    for _ in range(50):
        assert subscription.matches_result(sub1, set())
        assert not subscription.matches_result(sub2, set())
    end_time = datetime.datetime.now()
    print((end_time-start_time)/100)
    print(((end_time-start_time)/100).microseconds)
