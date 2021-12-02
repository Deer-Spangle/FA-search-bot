import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.inline_search import InlineSearchFunctionality
from fa_search_bot.sites.fa_handler import FAHandler
from fa_search_bot.tests.functionality.inline.utils import assert_answer_is_error
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent, _MockInlineBuilder


@pytest.mark.asyncio
async def test_empty_query_no_results(mock_client):
    event = MockTelegramEvent.with_inline_query(query="")
    handler = FAHandler(MockExportAPI())
    inline = InlineSearchFunctionality({
        handler.site_code: handler
    })

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_with([])


@pytest.mark.asyncio
async def test_simple_search(mock_client):
    post_id = 234563
    search_term = "YCH"
    event = MockTelegramEvent.with_inline_query(query=search_term)
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_search_results(search_term, [submission])
    handler = FAHandler(api)
    inline = InlineSearchFunctionality({
        handler.site_code: handler
    })

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] == "2"
    assert event.answer.call_args[1]['gallery'] is True
    assert isinstance(args[0], list)
    assert len(args[0]) > 0
    for result in args[0]:
        assert isinstance(result, _MockInlineBuilder._MockInlinePhoto)
        assert result.kwargs['file'] == submission.thumbnail_url
        assert result.kwargs['id'] == submission.submission_id
        assert result.kwargs['text'] == submission.link
        assert len(result.kwargs['buttons']) == 1
        assert result.kwargs['buttons'][0].data == f"neaten_me:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_no_search_results(mock_client):
    search_term = "RareKeyword"
    event = MockTelegramEvent.with_inline_query(query=search_term)
    api = MockExportAPI().with_search_results(search_term, [])
    handler = FAHandler(api)
    inline = InlineSearchFunctionality({
        handler.site_code: handler
    })

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    assert_answer_is_error(
        event.answer,
        "No results found.",
        f"No results for search \"{search_term}\"."
    )


@pytest.mark.asyncio
async def test_search_with_offset(mock_client):
    post_id = 234563
    search_term = "YCH"
    offset = 2
    event = MockTelegramEvent.with_inline_query(query=search_term, offset=str(offset))
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_search_results(search_term, [submission], page=offset)
    handler = FAHandler(api)
    inline = InlineSearchFunctionality({
        handler.site_code: handler
    })

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert isinstance(args[0], list)
    assert len(args[0]) > 0
    for result in args[0]:
        assert isinstance(result, _MockInlineBuilder._MockInlinePhoto)
        assert result.kwargs['file'] == submission.thumbnail_url
        assert result.kwargs['id'] == str(post_id)
        assert result.kwargs['text'] == submission.link
        assert len(result.kwargs['buttons']) == 1
        assert result.kwargs['buttons'][0].data == f"neaten_me:{post_id}".encode()


@pytest.mark.asyncio
async def test_search_with_offset_no_more_results(mock_client):
    search_term = "YCH"
    offset = 2
    event = MockTelegramEvent.with_inline_query(query=search_term, offset=str(offset))
    api = MockExportAPI().with_search_results(search_term, [], page=offset)
    handler = FAHandler(api)
    inline = InlineSearchFunctionality({
        handler.site_code: handler
    })

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] is None
    assert event.answer.call_args[1]['gallery'] is True
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
    api = MockExportAPI().with_search_results(search_term, [submission1, submission2])
    handler = FAHandler(api)
    inline = InlineSearchFunctionality({
        handler.site_code: handler
    })

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] == "2"
    assert event.answer.call_args[1]['gallery'] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 2
    for result in args[0]:
        assert isinstance(result, _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs['file'] == submission1.thumbnail_url
    assert args[0][0].kwargs['id'] == str(post_id1)
    assert args[0][0].kwargs['text'] == submission1.link
    assert len(args[0][0].kwargs['buttons']) == 1
    assert args[0][0].kwargs['buttons'][0].data == f"neaten_me:{submission1.submission_id}".encode()
    assert args[0][1].kwargs['file'] == submission2.thumbnail_url
    assert args[0][1].kwargs['id'] == str(post_id2)
    assert args[0][1].kwargs['text'] == submission2.link
    assert len(args[0][1].kwargs['buttons']) == 1
    assert args[0][1].kwargs['buttons'][0].data == f"neaten_me:{submission2.submission_id}".encode()


@pytest.mark.asyncio
async def test_search_with_combo_characters(mock_client):
    search_term = "(deer & !ych) | (dragon & !ych)"
    event = MockTelegramEvent.with_inline_query(query=search_term)
    post_id = 213231
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_search_results(search_term, [submission])
    handler = FAHandler(api)
    inline = InlineSearchFunctionality({
        handler.site_code: handler
    })

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] == "2"
    assert event.answer.call_args[1]['gallery'] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs['file'] == submission.thumbnail_url
    assert args[0][0].kwargs['id'] == str(post_id)
    assert args[0][0].kwargs['text'] == submission.link
    assert len(args[0][0].kwargs['buttons']) == 1
    assert args[0][0].kwargs['buttons'][0].data == f"neaten_me:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_search_with_field(mock_client):
    search_term = "@lower citrinelle"
    event = MockTelegramEvent.with_inline_query(query=search_term)
    post_id = 213231
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_search_results(search_term, [submission])
    handler = FAHandler(api)
    inline = InlineSearchFunctionality({
        handler.site_code: handler
    })

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] == "2"
    assert event.answer.call_args[1]['gallery'] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs['file'] == submission.thumbnail_url
    assert args[0][0].kwargs['id'] == str(post_id)
    assert args[0][0].kwargs['text'] == submission.link
    assert len(args[0][0].kwargs['buttons']) == 1
    assert args[0][0].kwargs['buttons'][0].data == f"neaten_me:{submission.submission_id}".encode()