from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from typing import Coroutine, List

T = TypeVar("T")


async def gather_ignore_exceptions(coros: List[Coroutine[None, None, T]]) -> List[T]:
    return list(
        filter(
            lambda x: not isinstance(x, Exception),
            await asyncio.gather(*coros, return_exceptions=True),
        )
    )
