from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from typing import Awaitable, List

T = TypeVar("T")


logger = logging.getLogger(__name__)


async def gather_ignore_exceptions(coros: List[Awaitable[T]]) -> List[T]:
    results = await asyncio.gather(*coros, return_exceptions=True)
    answers = []
    for result in results:
        if isinstance(result, Exception):
            logger.debug("Gathering results and hit exception, ignoring.", exc_info=result)
        else:
            answers.append(result)
    return answers


def regex_combine(*patterns: re.Pattern) -> re.Pattern:
    return re.compile("(" + "|".join(p.pattern for p in patterns) + ")", re.I)
