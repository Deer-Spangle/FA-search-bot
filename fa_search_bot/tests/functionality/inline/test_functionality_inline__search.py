import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.inline import InlineFunctionality
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent, _MockInlineBuilder


@pytest.mark.asyncio
async def test_empty_query_no_results(mock_client):
    event = MockTelegramEvent.with_inline_query(query="")
    inline = InlineFunctionality(MockExportAPI())

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_with([])


@pytest.mark.asyncio
async def test_simple_search(mock_client):
    post_id = 234563
    search_term = "YCH"
    event = MockTelegramEvent.with_inline_query(query=search_term)
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_search_results(search_term, [submission])

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] == "2"
    assert isinstance(args[0], list)
    assert len(args[0]) > 0
    for result in args[0]:
        assert isinstance(result, _MockInlineBuilder._MockInlinePhoto)
        assert result.kwargs == {
            "file": submission.thumbnail_url,
            "id": str(submission.submission_id),
            "text": submission.link,
        }


@pytest.mark.asyncio
async def test_no_search_results(mock_client):
    search_term = "RareKeyword"
    event = MockTelegramEvent.with_inline_query(query=search_term)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_search_results(search_term, [])

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] is None
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlineArticle)
    assert args[0][0].kwargs == {
        "title": "No results found.",
        "description": "No results for search \"{}\".".format(search_term)
    }


@pytest.mark.asyncio
async def test_search_with_offset(mock_client):
    post_id = 234563
    search_term = "YCH"
    offset = 2
    event = MockTelegramEvent.with_inline_query(query=search_term, offset=offset)
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_search_results(search_term, [submission], page=offset)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert isinstance(args[0], list)
    assert len(args[0]) > 0
    for result in args[0]:
        assert isinstance(result, _MockInlineBuilder._MockInlinePhoto)
        assert result.kwargs == {
            "id": str(post_id),
            "file": submission.thumbnail_url,
            "text": submission.link
        }


@pytest.mark.asyncio
async def test_search_with_offset_no_more_results(mock_client):
    search_term = "YCH"
    offset = 2
    event = MockTelegramEvent.with_inline_query(query=search_term, offset=offset)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_search_results(search_term, [], page=offset)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] is None
    assert isinstance(args[0], list)
    assert len(args[0]) == 0


@pytest.mark.asyncio
async def test_search_with_spaces(mock_client):
    search_term = "deer YCH"
    event = MockTelegramEvent.with_inline_query(query=search_term)
    post_id1 = 213231
    post_id2 = 84331
    submission1 = MockSubmission(post_id1)
    submission2 = MockSubmission(post_id2)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_search_results(search_term, [submission1, submission2])

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] == "2"
    assert isinstance(args[0], list)
    assert len(args[0]) == 2
    for result in args[0]:
        assert isinstance(result, _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs == {
        "id": str(post_id1),
        "file": submission1.thumbnail_url,
        "text": submission1.link,
    }
    assert args[0][1].kwargs == {
        "id": str(post_id2),
        "file": submission2.thumbnail_url,
        "text": submission2.link,
    }


@pytest.mark.asyncio
async def test_search_with_combo_characters(mock_client):
    search_term = "(deer & !ych) | (dragon & !ych)"
    event = MockTelegramEvent.with_inline_query(query=search_term)
    post_id = 213231
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_search_results(search_term, [submission])

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] == "2"
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs == {
        "id": str(post_id),
        "file": submission.thumbnail_url,
        "text": submission.link
    }


@pytest.mark.asyncio
async def test_search_with_field(mock_client):
    search_term = "@lower citrinelle"
    event = MockTelegramEvent.with_inline_query(query=search_term)
    post_id = 213231
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_search_results(search_term, [submission])

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] == "2"
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs == {
        "id": str(post_id),
        "file": submission.thumbnail_url,
        "text": submission.link,
    }
