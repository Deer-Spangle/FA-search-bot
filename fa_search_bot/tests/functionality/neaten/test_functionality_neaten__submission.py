import pytest
from telethon.events import StopPropagation

from fa_search_bot.sites.fa_export_api import CloudflareError
from fa_search_bot.sites.fa_submission import FASubmission
from fa_search_bot.functionalities.neaten import NeatenFunctionality
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent, MockButton, ChatType


@pytest.mark.asyncio
async def test_ignore_message(mock_client):
    event = MockTelegramEvent.with_message(text="hello world")
    neaten = NeatenFunctionality(MockExportAPI())

    await neaten.call(event)

    event.reply.assert_not_called()


@pytest.mark.asyncio
async def test_ignore_link(mock_client):
    event = MockTelegramEvent.with_message(text="http://example.com")
    neaten = NeatenFunctionality(MockExportAPI())

    await neaten.call(event)

    event.reply.assert_not_called()


@pytest.mark.asyncio
async def test_ignore_profile_link(mock_client):
    event = MockTelegramEvent.with_message(text="https://www.furaffinity.net/user/fender/")
    neaten = NeatenFunctionality(MockExportAPI())

    await neaten.call(event)

    event.reply.assert_not_called()


@pytest.mark.asyncio
async def test_ignore_journal_link(mock_client):
    event = MockTelegramEvent.with_message(text="https://www.furaffinity.net/journal/9150534/")
    neaten = NeatenFunctionality(MockExportAPI())

    await neaten.call(event)

    event.reply.assert_not_called()


@pytest.mark.asyncio
async def test_ignore_channel_post(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_channel_post(text=f"https://www.furaffinity.net/view/{post_id}/")
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    await neaten.call(event)

    submission._send_message.assert_not_called()


@pytest.mark.asyncio
async def test_submission_link(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
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
async def test_submission_link_in_caption(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        client=mock_client
    ).with_photo(caption=f"https://www.furaffinity.net/view/{post_id}/")
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
async def test_submission_group_chat(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=ChatType.GROUP,
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
async def test_submission_link_in_group_caption(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        chat_type=ChatType.GROUP
    ).with_photo(caption=f"https://www.furaffinity.net/view/{post_id}/")
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    await neaten.call(event)

    submission._send_message.assert_not_called()


@pytest.mark.asyncio
async def test_submission_link_in_group_caption(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        chat_type=ChatType.GROUP,
        text=f"https://www.furaffinity.net/view/{post_id}/"
    ).with_document()
    submission = MockSubmission(post_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

    await neaten.call(event)

    submission._send_message.assert_not_called()


@pytest.mark.asyncio
async def test_submission_link_no_http(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="furaffinity.net/view/{}".format(post_id),
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
async def test_two_submission_links(mock_client):
    post_id1 = 23636984
    post_id2 = 23636996
    event = MockTelegramEvent.with_message(
        text="furaffinity.net/view/{}\nfuraffinity.net/view/{}".format(post_id1, post_id2),
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


@pytest.mark.asyncio
async def test_duplicate_submission_links(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="furaffinity.net/view/{0}\nfuraffinity.net/view/{0}".format(post_id),
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
async def test_deleted_submission(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(text="furaffinity.net/view/{}".format(post_id))
    neaten = NeatenFunctionality(MockExportAPI())

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    event.reply.assert_called_with(
        f"This doesn't seem to be a valid FA submission: https://www.furaffinity.net/view/{post_id}/"
    )


@pytest.mark.asyncio
async def test_deleted_submission_group_chat(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(text="furaffinity.net/view/{}".format(post_id), chat_type=ChatType.GROUP)
    neaten = NeatenFunctionality(MockExportAPI())

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
async def test_pdf_submission(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_ext="pdf")
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
async def test_mp3_submission(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_ext="mp3")
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
async def test_txt_submission(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_ext="txt")
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
async def test_swf_submission(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=ChatType.PRIVATE,
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_ext="swf")
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
async def test_swf_submission_groupchat(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=ChatType.GROUP
    )
    submission = MockSubmission(post_id, file_ext="swf")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

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
async def test_unknown_type_submission_groupchat(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        chat_type=ChatType.GROUP
    )
    submission = MockSubmission(post_id, file_ext="zzz")
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_submission(submission)

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
async def test_link_in_button(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="Hello",
        client=mock_client,
    ).with_buttons(
        [
            [
                MockButton("View on E621", "https://e621.net/post/show/1699284"),
                MockButton("View on FA", f"https://www.furaffinity.net/view/{post_id}")
            ],
            [
                MockButton("Visit my website", "https://example.com")
            ]
        ]
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
async def test_image_just_under_size_limit(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_size=FASubmission.SIZE_LIMIT_IMAGE - 1)
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
async def test_image_just_over_size_limit(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_size=FASubmission.SIZE_LIMIT_IMAGE + 1)
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
async def test_image_over_document_size_limit(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_size=FASubmission.SIZE_LIMIT_DOCUMENT + 1)
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
async def test_auto_doc_just_under_size_limit(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_ext="pdf", file_size=FASubmission.SIZE_LIMIT_DOCUMENT - 1)
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
async def test_auto_doc_just_over_size_limit(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(
        text="https://www.furaffinity.net/view/{}/".format(post_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, file_ext="pdf", file_size=FASubmission.SIZE_LIMIT_DOCUMENT + 1)
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
async def test_cloudflare_error(mock_client):
    post_id = 23636984
    event = MockTelegramEvent.with_message(text="https://www.furaffinity.net/view/{}/".format(post_id))
    submission = MockSubmission(post_id)
    api = MockExportAPI()
    neaten = NeatenFunctionality(api)

    def raise_cloudflare(*args, **kwargs):
        raise CloudflareError()

    api.get_full_submission = raise_cloudflare

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    submission._send_message.assert_not_called()
    event.reply.assert_called_with(
        "Furaffinity returned a cloudflare error, so I cannot neaten links."
    )
