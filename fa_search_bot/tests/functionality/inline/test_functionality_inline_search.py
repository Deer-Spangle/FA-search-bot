import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.inline_search import InlineSearchFunctionality
from fa_search_bot.sites.e621.e621_handler import E621Handler
from fa_search_bot.sites.furaffinity.fa_handler import FAHandler
from fa_search_bot.sites.handler_group import HandlerGroup
from fa_search_bot.tests.functionality.inline.utils import assert_answer_is_error
from fa_search_bot.tests.util.mock_e621_client import MockAsyncYippiClient, MockPost
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_site_handler import MockSiteHandler
from fa_search_bot.tests.util.mock_submission_cache import MockSubmissionCache
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent, _MockInlineBuilder


@pytest.mark.asyncio
async def test_empty_query_no_results(mock_client):
    event = MockTelegramEvent.with_inline_query(query="")
    handler = FAHandler(MockExportAPI())
    cache = MockSubmissionCache()
    inline = InlineSearchFunctionality(HandlerGroup([handler], cache), cache)

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
    cache = MockSubmissionCache()
    inline = InlineSearchFunctionality(HandlerGroup([handler], cache), cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2:0"
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) > 0
    for result in args[0]:
        assert isinstance(result, _MockInlineBuilder._MockInlinePhoto)
        assert result.kwargs["file"] == submission.thumbnail_url
        assert result.kwargs["id"] == f"{handler.site_code}:{post_id}"
        assert result.kwargs["text"] == submission.link
        assert len(result.kwargs["buttons"]) == 1
        assert result.kwargs["buttons"][0].data == f"neaten_me:{handler.site_code}:{post_id}".encode()


@pytest.mark.asyncio
async def test_no_search_results(mock_client):
    search_term = "RareKeyword"
    event = MockTelegramEvent.with_inline_query(query=search_term)
    api = MockExportAPI().with_search_results(search_term, [])
    handler = FAHandler(api)
    cache = MockSubmissionCache()
    inline = InlineSearchFunctionality(HandlerGroup([handler], cache), cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    assert_answer_is_error(event.answer, "No results found.", f'No results for search "{search_term}".')


@pytest.mark.asyncio
async def test_search_with_offset(mock_client):
    post_id = 234563
    search_term = "YCH"
    page = 2
    offset = f"{page}:0"
    event = MockTelegramEvent.with_inline_query(query=search_term, offset=str(offset))
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_search_results(search_term, [submission], page=page)
    handler = FAHandler(api)
    cache = MockSubmissionCache()
    inline = InlineSearchFunctionality(HandlerGroup([handler], cache), cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert isinstance(args[0], list)
    assert len(args[0]) > 0
    for result in args[0]:
        assert isinstance(result, _MockInlineBuilder._MockInlinePhoto)
        assert result.kwargs["file"] == submission.thumbnail_url
        assert result.kwargs["id"] == f"{handler.site_code}:{post_id}"
        assert result.kwargs["text"] == submission.link
        assert len(result.kwargs["buttons"]) == 1
        assert result.kwargs["buttons"][0].data == f"neaten_me:{handler.site_code}:{post_id}".encode()


@pytest.mark.asyncio
async def test_search_with_offset_no_more_results(mock_client):
    search_term = "YCH"
    page = 2
    offset = f"{page}:0"
    event = MockTelegramEvent.with_inline_query(query=search_term, offset=offset)
    post_id = 234563
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_search_results(search_term, [submission], page=page - 1)
    handler = FAHandler(api)
    cache = MockSubmissionCache()
    inline = InlineSearchFunctionality(HandlerGroup([handler], cache), cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args.args
    assert event.answer.call_args.kwargs["next_offset"] is None
    assert event.answer.call_args.kwargs["gallery"] is True
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
    cache = MockSubmissionCache()
    inline = InlineSearchFunctionality(HandlerGroup([handler], cache), cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2:0"
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 2
    for result in args[0]:
        assert isinstance(result, _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs["file"] == submission1.thumbnail_url
    assert args[0][0].kwargs["id"] == f"{handler.site_code}:{submission1.submission_id}"
    assert args[0][0].kwargs["text"] == submission1.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:{handler.site_code}:{submission1.submission_id}".encode()
    assert args[0][1].kwargs["file"] == submission2.thumbnail_url
    assert args[0][1].kwargs["id"] == f"{handler.site_code}:{submission2.submission_id}"
    assert args[0][1].kwargs["text"] == submission2.link
    assert len(args[0][1].kwargs["buttons"]) == 1
    assert args[0][1].kwargs["buttons"][0].data == f"neaten_me:{handler.site_code}:{submission2.submission_id}".encode()


@pytest.mark.asyncio
async def test_search_with_combo_characters(mock_client):
    search_term = "(deer & !ych) | (dragon & !ych)"
    event = MockTelegramEvent.with_inline_query(query=search_term)
    post_id = 213231
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_search_results(search_term, [submission])
    handler = FAHandler(api)
    cache = MockSubmissionCache()
    inline = InlineSearchFunctionality(HandlerGroup([handler], cache), cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2:0"
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs["file"] == submission.thumbnail_url
    assert args[0][0].kwargs["id"] == f"{handler.site_code}:{submission.submission_id}"
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:{handler.site_code}:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_search_with_field(mock_client):
    search_term = "@lower citrinelle"
    event = MockTelegramEvent.with_inline_query(query=search_term)
    post_id = 213231
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_search_results(search_term, [submission])
    handler = FAHandler(api)
    cache = MockSubmissionCache()
    inline = InlineSearchFunctionality(HandlerGroup([handler], cache), cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2:0"
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs["file"] == submission.thumbnail_url
    assert args[0][0].kwargs["id"] == f"{handler.site_code}:{submission.submission_id}"
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:{handler.site_code}:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_search_site_prefix__letter(mock_client):
    site_letter = "f"
    site_name = "Furaffinity"
    search_term = "YCH"
    search_query = f"{site_letter}:{search_term}"
    event = MockTelegramEvent.with_inline_query(query=search_query)
    post_id = 213231
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_search_results(search_term, [submission])
    handler = MockSiteHandler(api, site_name=site_name, site_code="fa")
    cache = MockSubmissionCache()
    inline = InlineSearchFunctionality(HandlerGroup([handler], cache), cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2:0"
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs["file"] == submission.thumbnail_url
    assert args[0][0].kwargs["id"] == f"{handler.site_code}:{submission.submission_id}"
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:{handler.site_code}:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_search_site_prefix__code(mock_client):
    site_code = "fa"
    search_term = "YCH"
    search_query = f"{site_code}:{search_term}"
    event = MockTelegramEvent.with_inline_query(query=search_query)
    post_id = 213231
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_search_results(search_term, [submission])
    handler = MockSiteHandler(api, site_code=site_code)
    cache = MockSubmissionCache()
    inline = InlineSearchFunctionality(HandlerGroup([handler], cache), cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2:0"
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs["file"] == submission.thumbnail_url
    assert args[0][0].kwargs["id"] == f"{handler.site_code}:{submission.submission_id}"
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:{handler.site_code}:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_search_site_prefix__name(mock_client):
    site_name = "Furaffinity"
    search_term = "YCH"
    search_query = f"{site_name}:{search_term}"
    event = MockTelegramEvent.with_inline_query(query=search_query)
    post_id = 213231
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_search_results(search_term, [submission])
    handler = MockSiteHandler(api, site_name=site_name, site_code="fa")
    cache = MockSubmissionCache()
    inline = InlineSearchFunctionality(HandlerGroup([handler], cache), cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2:0"
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs["file"] == submission.thumbnail_url
    assert args[0][0].kwargs["id"] == f"{handler.site_code}:{post_id}"
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:{handler.site_code}:{post_id}".encode()


@pytest.mark.asyncio
async def test_search_site_prefix__name_lower(mock_client):
    site_name = "furaffinity"
    search_term = "YCH"
    search_query = f"{site_name.lower()}:{search_term}"
    event = MockTelegramEvent.with_inline_query(query=search_query)
    post_id = 213231
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_search_results(search_term, [submission])
    handler = MockSiteHandler(api, site_name=site_name, site_code="fa")
    cache = MockSubmissionCache()
    inline = InlineSearchFunctionality(HandlerGroup([handler], cache), cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2:0"
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs["file"] == submission.thumbnail_url
    assert args[0][0].kwargs["id"] == f"{handler.site_code}:{submission.submission_id}"
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:{handler.site_code}:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_search_site_prefix_e621(mock_client):
    search_term = "citrinelle"
    search_query = f"e621:{search_term}"
    event = MockTelegramEvent.with_inline_query(query=search_query)
    post_id = 213231
    post = MockPost(post_id=post_id, tags=["citrinelle"])
    api = MockAsyncYippiClient([post], page=1)
    handler = E621Handler(api)
    cache = MockSubmissionCache()
    inline = InlineSearchFunctionality(HandlerGroup([handler], cache), cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2:0"
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs["file"] == post._direct_thumb_link
    assert args[0][0].kwargs["id"] == f"{handler.site_code}:{post_id}"
    assert args[0][0].kwargs["text"] == post._post_link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:{handler.site_code}:{post_id}".encode()


@pytest.mark.asyncio
async def test_search_site_prefix_fa(mock_client):
    search_term = "citrinelle"
    search_query = f"fa:{search_term}"
    event = MockTelegramEvent.with_inline_query(query=search_query)
    post_id = 213231
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_search_results(search_term, [submission])
    handler = FAHandler(api)
    cache = MockSubmissionCache()
    inline = InlineSearchFunctionality(HandlerGroup([handler], cache), cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2:0"
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs["file"] == submission.thumbnail_url
    assert args[0][0].kwargs["id"] == f"{handler.site_code}:{submission.submission_id}"
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:{handler.site_code}:{submission.submission_id}".encode()
