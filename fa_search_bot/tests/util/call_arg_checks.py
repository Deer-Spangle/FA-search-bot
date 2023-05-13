import abc
from typing import List, Type


class CallArgCheck(abc.ABC):

    def __and__(self, other: "CallArgCheck") -> "CallArgAnd":
        return CallArgAnd([self, other])


class CallArgInstanceOf(CallArgCheck):
    def __init__(self, klass: Type):
        self.klass = klass

    def __eq__(self, other):
        return isinstance(other, self.klass)


class CallArgContains(CallArgCheck):
    def __init__(self, substr: str) -> None:
        self.substr = substr

    def __eq__(self, other):
        return isinstance(other, str) and self.substr in other


class CallArgAnd(CallArgCheck):
    def __init__(self, checks: List[CallArgCheck]):
        self.checks = checks

    def __eq__(self, other):
        return all(check.__eq__(other) for check in self.checks)
