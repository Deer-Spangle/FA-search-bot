from unittest.mock import AsyncMock

from fa_search_bot.tests.util.mock_telegram_event import _MockInlineBuilder


def assert_answer_is_error(answer: AsyncMock, title: str, desc: str) -> None:
    assert not answer.call_args[0]
    kwargs = answer.call_args[1]
    assert kwargs['next_offset'] is None
    assert kwargs['gallery'] is False
    assert isinstance(kwargs['results'], list)
    assert len(kwargs['results']) == 1
    assert isinstance(kwargs['results'][0], _MockInlineBuilder._MockInlineArticle)
    assert kwargs['results'][0].kwargs == {
        "title": title,
        "description": desc,
        "text": desc,
    }
