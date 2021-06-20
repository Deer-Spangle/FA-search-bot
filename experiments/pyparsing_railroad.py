import os
from pathlib import Path

from pyparsing.diagram import to_railroad, railroad_to_html

from fa_search_bot.query_parser import query_parser


def create_railroad_diagram() -> None:
    expr = query_parser()
    # Creating railroad diagrams
    railroad_path = Path(__file__).parent.parent / "docs" / "query_parser_railroad.html"
    with open(railroad_path, "w") as fp:
        railroad = to_railroad(expr)
        fp.write(railroad_to_html(railroad))


if __name__ == "__main__":
    create_railroad_diagram()
