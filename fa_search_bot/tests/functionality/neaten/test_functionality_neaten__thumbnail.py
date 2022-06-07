import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.neaten import NeatenFunctionality
from fa_search_bot.tests.util.mock_export_api import (MockExportAPI,
                                                      MockSubmission)
from fa_search_bot.tests.util.mock_site_handler import MockSiteHandler
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent


@pytest.mark.asyncio
async def test_thumbnail_link(mock_client):
    post_id = 382632
    event = MockTelegramEvent.with_message(
        text=f"https://t.furaffinity.net/{post_id}@400-1562445328.jpg",
        client=mock_client,
    )
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_thumbnail_link__old_cdn(mock_client):
    post_id = 382632
    event = MockTelegramEvent.with_message(
        text=f"https://t.facdn.net/{post_id}@400-1562445328.jpg",
        client=mock_client,
    )
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_thumbnail_link__newer_cdn(mock_client):
    post_id = 382632
    event = MockTelegramEvent.with_message(
        text=f"https://t2.facdn.net/{post_id}@400-1562445328.jpg",
        client=mock_client,
    )
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_thumbnail_link_not_round(mock_client):
    post_id = 382632
    event = MockTelegramEvent.with_message(
        text=f"https://t.furaffinity.net/{post_id}@75-1562445328.jpg",
        client=mock_client,
    )
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_thumbnail_link_big(mock_client):
    post_id = 382632
    event = MockTelegramEvent.with_message(
        text=f"https://t.furaffinity.net/{post_id}@1600-1562445328.jpg",
        client=mock_client,
    )
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_doesnt_fire_on_avatar(mock_client):
    event = MockTelegramEvent.with_message(
        text="https://a.furaffinity.net/1538326752/geordie79.gif",
        client=mock_client,
    )
    api = MockExportAPI()
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    await neaten.call(event)

    event.reply.assert_not_called()


@pytest.mark.asyncio
async def test_thumb_and_submission_link(mock_client):
    post_id = 382632
    event = MockTelegramEvent.with_message(
        text=f"https://t.furaffinity.net/{post_id}@1600-1562445328.jpg\nhttps://furaffinity.net/view/{post_id}",
        client=mock_client,
    )
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_thumb_and_different_submission_link(mock_client):
    post_id1 = 382632
    post_id2 = 382672
    event = MockTelegramEvent.with_message(
        text=f"https://t.furaffinity.net/{post_id1}@1600-1562445328.jpg\nhttps://furaffinity.net/view/{post_id2}",
        client=mock_client,
    )
    submission1 = MockSubmission(post_id1)
    submission2 = MockSubmission(post_id2)
    api = MockExportAPI().with_submissions([submission1, submission2])
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called()
    call1, call2 = handler._send_submission.call_args_list
    args1, kwargs1 = call1
    assert args1 == (post_id1, mock_client, event.input_chat)
    assert kwargs1['reply_to'] == event.message.id
    args2, kwargs2 = call2
    assert args2 == (post_id2, mock_client, event.input_chat)
    assert kwargs2['reply_to'] == event.message.id
