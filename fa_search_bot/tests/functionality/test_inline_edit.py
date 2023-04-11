import pytest

from fa_search_bot.functionalities.inline_edit import InlineEditButtonPress, InlineEditFunctionality
from fa_search_bot.sites.handler_group import HandlerGroup
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_site_handler import MockSiteHandler
from fa_search_bot.tests.util.mock_submission_cache import MockSubmissionCache
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent


@pytest.mark.asyncio
async def test_inline_edit_functionality__no_site_code(mock_client):
    post_id = 1234
    event = MockTelegramEvent.with_inline_send(result_id=str(post_id))
    sub = MockSubmission(1234)
    api = MockExportAPI().with_submission(sub)
    handler = MockSiteHandler(api, site_code="fa")
    cache = MockSubmissionCache()
    func = InlineEditFunctionality(HandlerGroup([handler], cache), mock_client)

    await func.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args[0] == str(post_id)
    assert args[1] == mock_client
    assert args[2] == event.msg_id
    assert kwargs["edit"] is True


@pytest.mark.asyncio
async def test_inline_edit_functionality__site_code(mock_client):
    post_id = 1234
    sub = MockSubmission(1234)
    api = MockExportAPI().with_submission(sub)
    handler = MockSiteHandler(api)
    event = MockTelegramEvent.with_inline_send(result_id=f"{handler.site_code}:{post_id}")
    cache = MockSubmissionCache()
    func = InlineEditFunctionality(HandlerGroup([handler], cache), mock_client)

    await func.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args[0] == str(post_id)
    assert args[1] == mock_client
    assert args[2] == event.msg_id
    assert kwargs["edit"] is True


@pytest.mark.asyncio
async def test_inline_edit_functionality__unknown_site_code(mock_client):
    post_id = 1234
    sub = MockSubmission(1234)
    api = MockExportAPI().with_submission(sub)
    handler = MockSiteHandler(api)
    event = MockTelegramEvent.with_inline_send(result_id=f"xy:{post_id}")
    cache = MockSubmissionCache()
    func = InlineEditFunctionality(HandlerGroup([handler], cache), mock_client)

    await func.call(event)

    handler._send_submission.assert_not_called()


@pytest.mark.asyncio
async def test_inline_button_press__no_site_code(mock_client):
    post_id = 1234
    callback = MockTelegramEvent.with_callback_query(
        data=f"neaten_me:{post_id}".encode(), client=mock_client
    ).with_inline_id(12345, 5431)
    sub = MockSubmission(post_id)
    api = MockExportAPI().with_submission(sub)
    handler = MockSiteHandler(api, site_code="fa")
    cache = MockSubmissionCache()
    func = InlineEditButtonPress(HandlerGroup([handler], cache))

    await func.call(callback)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args[0] == str(post_id)
    assert args[1] == mock_client
    assert args[2] == callback.original_update.msg_id
    assert kwargs["edit"] is True


@pytest.mark.asyncio
async def test_inline_button_press__site_code(mock_client):
    post_id = 1234
    sub = MockSubmission(post_id)
    api = MockExportAPI().with_submission(sub)
    handler = MockSiteHandler(api)
    callback = MockTelegramEvent.with_callback_query(
        data=f"neaten_me:{handler.site_code}:{post_id}".encode(), client=mock_client
    ).with_inline_id()
    cache = MockSubmissionCache()
    func = InlineEditButtonPress(HandlerGroup([handler], cache))

    await func.call(callback)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args[0] == str(post_id)
    assert args[1] == mock_client
    assert args[2] == callback.original_update.msg_id
    assert kwargs["edit"] is True


@pytest.mark.asyncio
async def test_inline_button_press__unknown_site_code(mock_client):
    post_id = 1234
    callback = MockTelegramEvent.with_callback_query(
        data=f"neaten_me:xy:{post_id}".encode(), client=mock_client
    ).with_inline_id()
    sub = MockSubmission(post_id)
    api = MockExportAPI().with_submission(sub)
    handler = MockSiteHandler(api)
    cache = MockSubmissionCache()
    func = InlineEditButtonPress(HandlerGroup([handler], cache))

    await func.call(callback)

    handler._send_submission.assert_not_called()
