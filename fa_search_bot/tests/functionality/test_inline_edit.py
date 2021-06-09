import pytest

from fa_search_bot.functionalities.inline_edit import InlineEditButtonPress, InlineEditFunctionality
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent


@pytest.mark.asyncio
async def test_inline_edit_functionality(mock_client):
    post_id = 1234
    event = MockTelegramEvent.with_inline_send(
        result_id=str(post_id)
    )
    sub = MockSubmission(1234)
    api = MockExportAPI().with_submission(sub)
    func = InlineEditFunctionality(api, mock_client)

    await func.call(event)

    sub._send_message.assert_called_once()
    args, kwargs = sub._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.msg_id
    assert kwargs['reply_to'] is None
    assert kwargs['edit'] is True


@pytest.mark.asyncio
async def test_inline_button_press(mock_client):
    callback = MockTelegramEvent.with_callback_query(
        data=b"neaten_me:1234",
        client=mock_client
    ).with_inline_id(12345, 5431)
    sub = MockSubmission(1234)
    api = MockExportAPI().with_submission(sub)
    func = InlineEditButtonPress(api)

    await func.call(callback)

    sub._send_message.assert_called_once()
    args, kwargs = sub._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == callback.original_update.msg_id
    assert kwargs['reply_to'] is None
    assert kwargs['edit'] is True
