import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.neaten import NeatenFunctionality
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent


@pytest.mark.asyncio
async def test_thumbnail_link(mock_client):
    post_id = 382632
    event = MockTelegramEvent.with_message(
        text=f"https://t.furaffinity.net/{post_id}@400-1562445328.jpg",
        client=mock_client,
    )
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    submission._send_message.assert_called_once()
    args, kwargs = submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_thumbnail_link__old_cdn(mock_client):
    post_id = 382632
    event = MockTelegramEvent.with_message(
        text=f"https://t.facdn.net/{post_id}@400-1562445328.jpg",
        client=mock_client,
    )
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    submission._send_message.assert_called_once()
    args, kwargs = submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_thumbnail_link__newer_cdn(mock_client):
    post_id = 382632
    event = MockTelegramEvent.with_message(
        text=f"https://t2.facdn.net/{post_id}@400-1562445328.jpg",
        client=mock_client,
    )
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    submission._send_message.assert_called_once()
    args, kwargs = submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_thumbnail_link_not_round(mock_client):
    post_id = 382632
    event = MockTelegramEvent.with_message(
        text=f"https://t.furaffinity.net/{post_id}@75-1562445328.jpg",
        client=mock_client,
    )
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    submission._send_message.assert_called_once()
    args, kwargs = submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_thumbnail_link_big(mock_client):
    post_id = 382632
    event = MockTelegramEvent.with_message(
        text=f"https://t.furaffinity.net/{post_id}@1600-1562445328.jpg",
        client=mock_client,
    )
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    submission._send_message.assert_called_once()
    args, kwargs = submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_doesnt_fire_on_avatar(mock_client):
    event = MockTelegramEvent.with_message(
        text="https://a.furaffinity.net/1538326752/geordie79.gif",
        client=mock_client,
    )
    neaten = NeatenFunctionality(MockExportAPI())

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
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    submission._send_message.assert_called_once()
    args, kwargs = submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
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
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submissions([submission1, submission2])

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    submission1._send_message.assert_called_once()
    args1, kwargs1 = submission1._send_message.call_args
    assert args1[0] == mock_client
    assert args1[1] == event.input_chat
    assert kwargs1['reply_to'] == event.message.id
    submission2._send_message.assert_called_once()
    args2, kwargs2 = submission2._send_message.call_args
    assert args2[0] == mock_client
    assert args2[1] == event.input_chat
    assert kwargs2['reply_to'] == event.message.id
