from pyparsing.diagram import to_railroad, railroad_to_html

from query_parser import query_parser


def create_railroad_diagram() -> None:
    expr = query_parser()
    # Creating railroad diagrams
    with open("experiments/output.html", "w") as fp:
        railroad = to_railroad(expr)
        fp.write(railroad_to_html(railroad))
