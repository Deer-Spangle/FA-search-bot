import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.inline_neaten import InlineNeatenFunctionality
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent, _MockInlineBuilder


@pytest.mark.asyncio
async def test_submission_id():
    post_id = 12345
    sub = MockSubmission(post_id)
    event = MockTelegramEvent.with_inline_query(query=str(post_id))
    inline = InlineNeatenFunctionality(
        MockExportAPI().with_submissions([
            MockSubmission(12344),
            sub,
            MockSubmission(12346)
        ])
    )

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args, kwargs = event.answer.call_args
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert kwargs['gallery'] is True
    result = args[0][0]
    assert isinstance(result, _MockInlineBuilder._MockInlinePhoto)
    assert result.kwargs == {
        "id": str(post_id),
        "file": sub.thumbnail_url,
        "text": sub.link
    }


@pytest.mark.asyncio
async def test_submission_id__no_result():
    post_id = 12345
    event = MockTelegramEvent.with_inline_query(query=str(post_id))
    inline = InlineNeatenFunctionality(
        MockExportAPI().with_submissions([
            MockSubmission(12344),
            MockSubmission(12346)
        ])
    )

    await inline.call(event)

    event.answer.assert_not_called()


@pytest.mark.asyncio
async def test_submission_link():
    post_id = 12345
    sub = MockSubmission(post_id)
    event = MockTelegramEvent.with_inline_query(query=sub.link)
    inline = InlineNeatenFunctionality(
        MockExportAPI().with_submissions([
            MockSubmission(12344),
            sub,
            MockSubmission(12346)
        ])
    )

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args, kwargs = event.answer.call_args
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert kwargs['gallery'] is True
    result = args[0][0]
    assert isinstance(result, _MockInlineBuilder._MockInlinePhoto)
    assert result.kwargs == {
        "id": str(post_id),
        "file": sub.thumbnail_url,
        "text": sub.link
    }


@pytest.mark.asyncio
async def test_submission_link__no_result():
    post_id = 12345
    sub = MockSubmission(post_id)
    event = MockTelegramEvent.with_inline_query(query=sub.link)
    inline = InlineNeatenFunctionality(
        MockExportAPI().with_submissions([
            MockSubmission(12344),
            MockSubmission(12346)
        ])
    )

    await inline.call(event)

    event.answer.assert_not_called()


@pytest.mark.asyncio
async def test_submission_direct_link():
    post_id = 12345
    sub = MockSubmission(post_id)
    event = MockTelegramEvent.with_inline_query(query=sub.download_url)
    inline = InlineNeatenFunctionality(
        MockExportAPI().with_user_folder(
            sub.username,
            "gallery",
            [
                MockSubmission(12344),
                sub,
                MockSubmission(12346)
            ]
        )
    )

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args, kwargs = event.answer.call_args
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert kwargs['gallery'] is True
    result = args[0][0]
    assert isinstance(result, _MockInlineBuilder._MockInlinePhoto)
    assert result.kwargs == {
        "id": str(post_id),
        "file": sub.thumbnail_url,
        "text": sub.link
    }


@pytest.mark.asyncio
async def test_submission_direct_link__not_found():
    post_id = 12345
    sub = MockSubmission(post_id)
    event = MockTelegramEvent.with_inline_query(query=sub.download_url)
    inline = InlineNeatenFunctionality(
        MockExportAPI().with_user_folder(
            sub.username,
            "gallery",
            [
                MockSubmission(12344),
                MockSubmission(12346)
            ]
        )
    )

    await inline.call(event)

    event.answer.assert_not_called()


@pytest.mark.asyncio
async def test_query_not_id_or_link():
    post_id = 12345
    sub = MockSubmission(post_id)
    event = MockTelegramEvent.with_inline_query(query="test")
    inline = InlineNeatenFunctionality(
        MockExportAPI().with_submissions([
            MockSubmission(12344),
            sub,
            MockSubmission(12346)
        ])
    )

    await inline.call(event)

    event.answer.assert_not_called()
