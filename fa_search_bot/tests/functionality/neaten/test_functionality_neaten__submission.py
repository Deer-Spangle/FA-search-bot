import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.neaten import NeatenFunctionality
from fa_search_bot.sites.furaffinity.fa_export_api import CloudflareError
from fa_search_bot.sites.furaffinity.fa_handler import FAHandler
from fa_search_bot.sites.sendable import Sendable
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_site_handler import MockSiteHandler
from fa_search_bot.tests.util.mock_telegram_event import ChatType, MockButton, MockTelegramEvent


@pytest.mark.asyncio
async def test_ignore_message(mock_client):
    event = MockTelegramEvent.with_message(text="hello world")
    handler = MockSiteHandler(MockExportAPI())
    neaten = NeatenFunctionality({handler.site_code: handler})

    await neaten.call(event)

    event.reply.assert_not_called()


@pytest.mark.asyncio
async def test_ignore_link(mock_client):
    event = MockTelegramEvent.with_message(text="https://example.com")
    handler = MockSiteHandler(MockExportAPI())
    neaten = NeatenFunctionality({handler.site_code: handler})

    await neaten.call(event)

    event.reply.assert_not_called()


@pytest.mark.asyncio
async def test_ignore_profile_link(mock_client):
    event = MockTelegramEvent.with_message(text="https://www.furaffinity.net/user/fender/")
    handler = MockSiteHandler(MockExportAPI())
    neaten = NeatenFunctionality({handler.site_code: handler})

    await neaten.call(event)

    event.reply.assert_not_called()


@pytest.mark.asyncio
async def test_ignore_journal_link(mock_client):
    event = MockTelegramEvent.with_message(text="https://www.furaffinity.net/journal/9150534/")
    handler = MockSiteHandler(MockExportAPI())
    neaten = NeatenFunctionality({handler.site_code: handler})

    await neaten.call(event)

    event.reply.assert_not_called()


@pytest.mark.asyncio
async def test_ignore_channel_post(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_channel_post(text=f"https://www.furaffinity.net/view/{post_id}/")
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    await neaten.call(event)

    handler._send_submission.assert_not_called()


@pytest.mark.asyncio
async def test_submission_link(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
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
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_submission_link_in_caption(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(client=mock_client).with_photo(
        caption=f"https://www.furaffinity.net/view/{post_id}/"
    )
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args[0] == post_id
    assert args[1] == mock_client
    assert args[2] == event.input_chat
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_submission_group_chat(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=ChatType.GROUP,
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
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_submission_link_in_group_caption(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(chat_type=ChatType.GROUP).with_photo(
        caption=f"https://www.furaffinity.net/view/{post_id}/"
    )
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    await neaten.call(event)

    handler._send_submission.assert_not_called()


@pytest.mark.asyncio
async def test_submission_link_in_group_document_caption(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        chat_type=ChatType.GROUP, text=f"https://www.furaffinity.net/view/{post_id}/"
    ).with_document()
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    await neaten.call(event)

    handler._send_submission.assert_not_called()


@pytest.mark.asyncio
async def test_submission_link_no_http(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="furaffinity.net/view/{}".format(post_id),
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
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_two_submission_links(mock_client):
    post_id1 = 23636984
    post_id2 = 23636996
    event = MockTelegramEvent.with_message(
        text="furaffinity.net/view/{}\nfuraffinity.net/view/{}".format(post_id1, post_id2),
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
    assert kwargs1["reply_to"] == event.message.id
    args2, kwargs2 = call2
    assert args2 == (post_id2, mock_client, event.input_chat)
    assert kwargs2["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_duplicate_submission_links(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="furaffinity.net/view/{0}\nfuraffinity.net/view/{0}".format(post_id),
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
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_deleted_submission(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(text="furaffinity.net/view/{}".format(post_id))
    handler = FAHandler(MockExportAPI())
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    event.reply.assert_called_with(
        f"This doesn't seem to be a valid Furaffinity submission: https://www.furaffinity.net/view/{post_id}/"
    )


@pytest.mark.asyncio
async def test_deleted_submission_group_chat(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(text="furaffinity.net/view/{}".format(post_id), chat_type=ChatType.GROUP)
    handler = MockSiteHandler(MockExportAPI())
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    event.reply.assert_called_with("⏳ Neatening image link")
    event.reply.return_value.delete.assert_called_once()


@pytest.mark.asyncio
async def test_gif_submission(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_ext="gif")
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_pdf_submission(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_ext="pdf")
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_mp3_submission(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_ext="mp3")
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_txt_submission(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_ext="txt")
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_swf_submission(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=ChatType.PRIVATE,
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_ext="swf")
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_swf_submission_groupchat(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=ChatType.GROUP,
    )
    submission = MockSubmission(post_id, file_ext="swf")
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    event.reply.assert_called_with(
        "⏳ Neatening image link",
    )
    event.reply.return_value.delete.assert_called_once()


@pytest.mark.asyncio
async def test_unknown_type_submission(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=ChatType.PRIVATE,
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_ext="zzz")
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_unknown_type_submission_groupchat(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=ChatType.GROUP,
    )
    submission = MockSubmission(post_id, file_ext="zzz")
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    event.reply.assert_called_with(
        "⏳ Neatening image link",
    )
    event.reply.return_value.delete.assert_called_once()


@pytest.mark.asyncio
async def test_link_in_markdown(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="[Hello](https://www.furaffinity.net/view/{}/)".format(post_id),
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
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_link_in_button(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(text="Hello", client=mock_client,).with_buttons(
        [
            [
                MockButton("View on E621", "https://e621.net/post/show/1699284"),
                MockButton("View on FA", f"https://www.furaffinity.net/view/{post_id}"),
            ],
            [MockButton("Visit my website", "https://example.com")],
        ]
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
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_image_just_under_size_limit(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_size=Sendable.SIZE_LIMIT_IMAGE - 1)
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_image_just_over_size_limit(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_size=Sendable.SIZE_LIMIT_IMAGE + 1)
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_image_over_document_size_limit(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_size=Sendable.SIZE_LIMIT_DOCUMENT + 1)
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_auto_doc_just_under_size_limit(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_ext="pdf", file_size=Sendable.SIZE_LIMIT_DOCUMENT - 1)
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_auto_doc_just_over_size_limit(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_ext="pdf", file_size=Sendable.SIZE_LIMIT_DOCUMENT + 1)
    api = MockExportAPI().with_submission(submission)
    handler = MockSiteHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    handler._send_submission.assert_called_once()
    args, kwargs = handler._send_submission.call_args
    assert args == (post_id, mock_client, event.input_chat)
    assert kwargs["reply_to"] == event.message.id


@pytest.mark.asyncio
async def test_cloudflare_error(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
    api = MockExportAPI()
    handler = FAHandler(api)
    neaten = NeatenFunctionality({handler.site_code: handler})

    def raise_cloudflare(*args, **kwargs):
        raise CloudflareError()

    api.get_full_submission = raise_cloudflare

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    event.reply.assert_called_with("Furaffinity returned a cloudflare error, so I cannot neaten links.")
