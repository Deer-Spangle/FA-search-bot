import os

from pyparsing.diagram import to_railroad, railroad_to_html

from fa_search_bot.query_parser import query_parser


def create_railroad_diagram() -> None:
    expr = query_parser()
    # Creating railroad diagrams
    with open("../docs/query_parser_railroad.html", "w") as fp:
        railroad = to_railroad(expr)
        fp.write(railroad_to_html(railroad))


if __name__ == "__main__":
    create_railroad_diagram()
