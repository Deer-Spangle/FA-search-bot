import re
from abc import ABC, abstractmethod
from typing import List, Optional

import pyparsing
import pytest
from pyparsing import Word, QuotedString, printables, Literal, Forward, ZeroOrMore, Group, \
    ParseResults, ParseException, CaselessLiteral, ParserElement
from pyparsing.diagram import to_railroad, railroad_to_html

from fa_submission import FASubmissionFull, Rating
from subscription_watcher import rating_dict


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

    def __repr__(self):
        return self.__class__.__name__


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
                and all(self.sub_queries[i] == other.sub_queries[i] for i in range(len(self.sub_queries)))
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


def query_parser() -> ParserElement:
    # Creating the grammar
    valid_chars = printables.replace("(", "").replace(")", "").replace(":", "").replace("\"", "")
    expr = Forward().setName("expression")
    quotes = QuotedString('"', "\\").setName("quoted string").setResultsName("quotes")
    brackets = Group(Literal("(").suppress() + expr + Literal(")").suppress())\
        .setName("bracketed expression").setResultsName("brackets")
    words = Word(valid_chars).setName("word").setResultsName("word")
    field_name = Group((Literal("@").suppress() + Word(valid_chars)) | (Word(valid_chars) + Literal(":").suppress()))\
        .setName("field name").setResultsName("field_name")
    field_value = Group(quotes | words).setName("field value").setResultsName("field_value")
    field = Group(field_name + field_value).setName("field").setResultsName("field")
    negator = Group(pyparsing.Optional(Literal("!") | Literal("-") | CaselessLiteral("not")))\
        .setName("negator").setResultsName("negator")
    element = Group(quotes | brackets | field | words).setName("element").setResultsName("element")
    full_element = Group(negator + element).setName("full element").setResultsName("full_element", listAllMatches=True)
    connector = Group(pyparsing.Optional(CaselessLiteral("or") | CaselessLiteral("and")))\
        .setName("connector").setResultsName("connector", listAllMatches=True)
    expr <<= full_element + ZeroOrMore(connector + full_element)
    return expr


def create_railroad_diagram() -> None:
    expr = query_parser()
    # Creating railroad diagrams
    with open("output.html", "w") as fp:
        railroad = to_railroad(expr)
        fp.write(railroad_to_html(railroad))


def parse_query(query_str: str) -> 'Query':
    expr = query_parser()
    # Parsing input
    try:
        parsed = expr.parseString(query_str, parseAll=True)
    except ParseException as e:
        raise InvalidQueryException(f"ParseException was thrown: {e}")
    # Turning into query
    return parse_expression(parsed)


def parse_expression(parsed: ParseResults) -> 'Query':
    result = parse_full_element(parsed.full_element[0])
    num_connectors = len(parsed.connector)
    for i in range(num_connectors):
        connector = parsed.connector[i]
        full_element = parse_full_element(parsed.full_element[i + 1])
        result = parse_connector(connector, result, full_element)
    return result


def parse_connector(parsed: ParseResults, query1: 'Query', query2: 'Query') -> 'Query':
    if not parsed:
        return AndQuery([query1, query2])
    if parsed[0].lower() == "and":
        return AndQuery([query1, query2])
    if parsed[0].lower() == "or":
        return OrQuery([query1, query2])
    raise InvalidQueryException(f"I do not recognise this connector: {parsed}")


def parse_full_element(parsed: ParseResults) -> 'Query':
    if not parsed.negator:
        return parse_element(parsed.element)
    return NotQuery(parse_element(parsed.element))


def parse_element(parsed: ParseResults) -> 'Query':
    if parsed.quotes:
        return parse_quotes(parsed.quotes)
    if parsed.brackets:
        return parse_expression(parsed.brackets)
    if parsed.field:
        return parse_field(parsed.field)
    if parsed.word:
        return parse_word(parsed.word)
    raise InvalidQueryException(f"I do not recognise this element: {parsed}")


def parse_quotes(phrase: str, field: Optional['Field'] = None) -> 'Query':
    return PhraseQuery(phrase, field)


def parse_field(parsed: ParseResults) -> 'Query':
    field_name = parsed.field_name[0]
    field_value = parsed.field_value
    if field_name.lower() == "rating":
        return parse_rating_field(field_value)
    field = parse_field_name(field_name)
    if field_value.quotes:
        return parse_quotes(field_value.quotes, field)
    if field_value.word:
        return parse_word(field_value.word, field)
    raise InvalidQueryException(f"Unrecognised field value {field_value}")


def parse_rating_field(field_value: ParseResults) -> 'Query':
    if field_value.quotes:
        raise InvalidQueryException("Rating field cannot be a quote")
    rating = rating_dict.get(field_value.word)
    if rating is None:
        raise InvalidQueryException(f"Unrecognised rating field value: {field_value.word}")
    return RatingQuery(rating)


def parse_field_name(field_name: str) -> 'Field':
    if field_name.lower() == "title":
        return TitleField()
    if field_name.lower() == "description":
        return DescriptionField()
    if field_name.lower() in ["keywords", "keyword"]:
        return KeywordField()
    raise InvalidQueryException(f"Unrecognised field name: {field_name}")


def parse_word(word: str, field: Optional['Field'] = None) -> 'Query':
    if word.startswith("*"):
        return SuffixQuery(word[1:], field)
    if word.endswith("*"):
        return PrefixQuery(word[:-1], field)
    if "*" in word:
        word_split = word.split("*")
        parts = [re.escape(part) for part in word_split]
        regex = ".*".join(parts)
        return RegexQuery(regex, field)
    return WordQuery(word, field)


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
