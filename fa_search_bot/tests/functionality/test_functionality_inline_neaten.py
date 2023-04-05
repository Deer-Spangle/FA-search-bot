import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.inline_neaten import InlineNeatenFunctionality
from fa_search_bot.sites.furaffinity.fa_handler import FAHandler
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent, _MockInlineBuilder


@pytest.mark.asyncio
async def test_submission_id():
    post_id = 12345
    sub = MockSubmission(post_id)
    event = MockTelegramEvent.with_inline_query(query=str(post_id))
    handler = FAHandler(MockExportAPI().with_submissions([MockSubmission(12344), sub, MockSubmission(12346)]))
    inline = InlineNeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args, kwargs = event.answer.call_args
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert kwargs["gallery"] is True
    result = args[0][0]
    assert isinstance(result, _MockInlineBuilder._MockInlinePhoto)
    assert result.kwargs["file"] == sub.thumbnail_url
    assert result.kwargs["id"] == f"{handler.site_code}:{post_id}"
    assert result.kwargs["text"] == sub.link
    assert len(result.kwargs["buttons"]) == 1
    assert result.kwargs["buttons"][0].data == f"neaten_me:{handler.site_code}:{post_id}".encode()


@pytest.mark.asyncio
async def test_submission_id__no_result():
    post_id = 12345
    event = MockTelegramEvent.with_inline_query(query=str(post_id))
    handler = FAHandler(MockExportAPI().with_submissions([MockSubmission(12344), MockSubmission(12346)]))
    inline = InlineNeatenFunctionality({handler.site_code: handler})

    await inline.call(event)

    event.answer.assert_not_called()


@pytest.mark.asyncio
async def test_submission_link():
    post_id = 12345
    sub = MockSubmission(post_id)
    event = MockTelegramEvent.with_inline_query(query=sub.link)
    handler = FAHandler(MockExportAPI().with_submissions([MockSubmission(12344), sub, MockSubmission(12346)]))
    inline = InlineNeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args, kwargs = event.answer.call_args
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert kwargs["gallery"] is True
    result = args[0][0]
    assert isinstance(result, _MockInlineBuilder._MockInlinePhoto)
    assert result.kwargs["file"] == sub.thumbnail_url
    assert result.kwargs["id"] == f"{handler.site_code}:{post_id}"
    assert result.kwargs["text"] == sub.link
    assert len(result.kwargs["buttons"]) == 1
    assert result.kwargs["buttons"][0].data == f"neaten_me:{handler.site_code}:{post_id}".encode()


@pytest.mark.asyncio
async def test_submission_link__no_result():
    post_id = 12345
    sub = MockSubmission(post_id)
    event = MockTelegramEvent.with_inline_query(query=sub.link)
    handler = FAHandler(MockExportAPI().with_submissions([MockSubmission(12344), MockSubmission(12346)]))
    inline = InlineNeatenFunctionality({handler.site_code: handler})

    await inline.call(event)

    event.answer.assert_not_called()


@pytest.mark.asyncio
async def test_submission_direct_link():
    post_id = 12345
    image_id = 98765434
    username = "fender"
    sub = MockSubmission(post_id, username=username, image_id=image_id)
    event = MockTelegramEvent.with_inline_query(query=sub.download_url)
    handler = FAHandler(
        MockExportAPI().with_user_folder(
            username,
            "gallery",
            [
                MockSubmission(12346, image_id=image_id + 50),
                sub,
                MockSubmission(12344, image_id=image_id - 50),
            ],
        )
    )
    inline = InlineNeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args, kwargs = event.answer.call_args
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert kwargs["gallery"] is True
    result = args[0][0]
    assert isinstance(result, _MockInlineBuilder._MockInlinePhoto)
    assert result.kwargs["file"] == sub.thumbnail_url
    assert result.kwargs["id"] == f"{handler.site_code}:{post_id}"
    assert result.kwargs["text"] == sub.link
    assert len(result.kwargs["buttons"]) == 1
    assert result.kwargs["buttons"][0].data == f"neaten_me:{handler.site_code}:{post_id}".encode()


@pytest.mark.asyncio
async def test_submission_direct_link__not_found():
    post_id = 12345
    username = "fender"
    sub = MockSubmission(post_id, username=username)
    event = MockTelegramEvent.with_inline_query(query=sub.download_url)
    handler = FAHandler(
        MockExportAPI().with_user_folder(username, "gallery", [MockSubmission(12344), MockSubmission(12346)])
    )
    inline = InlineNeatenFunctionality({handler.site_code: handler})

    await inline.call(event)

    event.answer.assert_not_called()


@pytest.mark.asyncio
async def test_query_not_id_or_link():
    post_id = 12345
    sub = MockSubmission(post_id)
    event = MockTelegramEvent.with_inline_query(query="test")
    handler = FAHandler(MockExportAPI().with_submissions([MockSubmission(12344), sub, MockSubmission(12346)]))
    inline = InlineNeatenFunctionality({handler.site_code: handler})

    await inline.call(event)

    event.answer.assert_not_called()
