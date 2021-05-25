import pytest
from telegram import Chat
from telethon.events import StopPropagation

from fa_search_bot.functionalities.neaten import NeatenFunctionality
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent


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
async def test_direct_link(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id),
        client=mock_client
    )
    goal_submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        goal_submission,
        MockSubmission(post_id - 1, image_id=image_id - 15)
    ])

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    goal_submission._send_message.assert_called_once()
    args, kwargs = goal_submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_direct_link__old_cdn(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id),
        client=mock_client
    )
    goal_submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        goal_submission,
        MockSubmission(post_id - 1, image_id=image_id - 15)
    ])

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    goal_submission._send_message.assert_called_once()
    args, kwargs = goal_submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_direct_link__newer_cdn(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d2.facdn.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id),
        client=mock_client
    )
    goal_submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        goal_submission,
        MockSubmission(post_id - 1, image_id=image_id - 15)
    ])

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    goal_submission._send_message.assert_called_once()
    args, kwargs = goal_submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_direct_in_progress_message(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    goal_submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        goal_submission,
        MockSubmission(post_id - 1, image_id=image_id - 15)
    ])

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    event.reply.assert_called_with("⏳ Neatening image link")
    event.reply.return_value.delete.assert_called_once()


@pytest.mark.asyncio
async def test_direct_in_progress_message_groupchat(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    goal_submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        goal_submission,
        MockSubmission(post_id - 1, image_id=image_id - 15)
    ])

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    event.reply.assert_called_with("⏳ Neatening image link")
    event.reply.return_value.delete.assert_called_once()


@pytest.mark.asyncio
async def test_direct_no_match(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    neaten = NeatenFunctionality(MockExportAPI())
    for folder in ['gallery', 'scraps']:
        neaten.api.with_user_folder(username, folder, [
            MockSubmission(post_id, image_id=image_id + 4),
            MockSubmission(post_id - 1, image_id=image_id - 15)
        ])

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    event.reply.assert_called()
    event.reply.assert_called_with(
        "Could not locate the image by {} with image id {}.".format(username, image_id)
    )


@pytest.mark.asyncio
async def test_direct_no_match_groupchat(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id),
        chat_type=Chat.GROUP
    )
    neaten = NeatenFunctionality(MockExportAPI())
    for folder in ['gallery', 'scraps']:
        neaten.api.with_user_folder(username, folder, [
            MockSubmission(post_id, image_id=image_id + 4),
            MockSubmission(post_id - 1, image_id=image_id - 15)
        ])

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    event.reply.assert_called_with("⏳ Neatening image link")
    event.reply.return_value.delete.assert_called_once()


@pytest.mark.asyncio
async def test_two_direct_links(mock_client):
    username = "fender"
    image_id1 = 1560331512
    image_id2 = 1560331510
    post_id1 = 232347
    post_id2 = 232346
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png "
             "http://d.facdn.net/art/{0}/{2}/{2}.pic_of_you.png".format(username, image_id1, image_id2),
        client=mock_client,
    )
    submission1 = MockSubmission(post_id1, image_id=image_id1)
    submission2 = MockSubmission(post_id2, image_id=image_id2)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        submission1,
        submission2,
        MockSubmission(post_id2 - 1, image_id=image_id2 - 15)
    ])

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
async def test_duplicate_direct_link(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png ".format(username, image_id) * 2,
        client=mock_client,
    )
    submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        submission,
        MockSubmission(post_id - 1, image_id=image_id - 15)
    ])

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    submission._send_message.assert_called_once()
    args, kwargs = submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_direct_link_and_matching_submission_link(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png https://furaffinity.net/view/{2}/".format(
            username, image_id, post_id
        ),
        client=mock_client,
    )
    submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        submission,
        MockSubmission(post_id - 1, image_id=image_id - 15)
    ])

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    submission._send_message.assert_called_once()
    args, kwargs = submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_direct_link_and_different_submission_link(mock_client):
    username = "fender"
    image_id1 = 1560331512
    image_id2 = image_id1 + 300
    post_id1 = 232347
    post_id2 = 233447
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png https://furaffinity.net/view/{2}/".format(
            username, image_id1, post_id2
        ),
        client=mock_client
    )
    submission1 = MockSubmission(post_id1, image_id=image_id1)
    submission2 = MockSubmission(post_id2, image_id=image_id2)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        submission2,
        submission1,
        MockSubmission(post_id1 - 1, image_id=image_id1 - 15)
    ])

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
async def test_submission_link_and_different_direct_link(mock_client):
    username = "fender"
    image_id1 = 1560331512
    image_id2 = image_id1 + 300
    post_id1 = 232347
    post_id2 = 233447
    event = MockTelegramEvent.with_message(
        text="https://furaffinity.net/view/{2}/ http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png".format(
            username, image_id1, post_id2
        ),
        client=mock_client
    )
    submission1 = MockSubmission(post_id1, image_id=image_id1)
    submission2 = MockSubmission(post_id2, image_id=image_id2)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        submission2,
        submission1,
        MockSubmission(post_id1 - 1, image_id=image_id1 - 15)
    ])

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
async def test_result_on_first_page(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        MockSubmission(post_id + 1, image_id=image_id + 16),
        submission,
        MockSubmission(post_id - 2, image_id=image_id - 27),
        MockSubmission(post_id - 3, image_id=image_id - 34)
    ])

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    submission._send_message.assert_called_once()
    args, kwargs = submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_result_on_third_page(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id),
        client=mock_client,
    )
    neaten = NeatenFunctionality(MockExportAPI())
    for page in [1, 2, 3]:
        neaten.api.with_user_folder(username, "gallery", [
            MockSubmission(post_id + 1 + (3 - page) * 5, image_id=image_id + 16 + (3 - page) * 56),
            MockSubmission(post_id + (3 - page) * 5, image_id=image_id + (3 - page) * 56),
            MockSubmission(post_id - 2 + (3 - page) * 5, image_id=image_id - 27 + (3 - page) * 56),
            MockSubmission(post_id - 3 + (3 - page) * 5, image_id=image_id - 34 + (3 - page) * 56)
        ], page=page)
    submission = await neaten.api.get_full_submission(str(post_id))

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    submission._send_message.assert_called_once()
    args, kwargs = submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_result_missing_from_first_page(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        MockSubmission(post_id + 1, image_id=image_id + 16),
        MockSubmission(post_id, image_id=image_id + 3),
        MockSubmission(post_id - 2, image_id=image_id - 27),
        MockSubmission(post_id - 3, image_id=image_id - 34)
    ])

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    event.reply.assert_called_with(
        "Could not locate the image by {} with image id {}.".format(username, image_id),
    )


@pytest.mark.asyncio
async def test_result_missing_from_second_page(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    neaten = NeatenFunctionality(MockExportAPI())
    for page in [1, 2]:
        neaten.api.with_user_folder(username, "gallery", [
            MockSubmission(post_id + 1 + (2 - page) * 6, image_id=image_id + 16 + (2 - page) * 56),
            MockSubmission(post_id + 0 + (2 - page) * 6, image_id=image_id + 3 + (2 - page) * 56),
            MockSubmission(post_id - 2 + (2 - page) * 6, image_id=image_id - 27 + (2 - page) * 56),
            MockSubmission(post_id - 3 + (2 - page) * 6, image_id=image_id - 34 + (2 - page) * 56)
        ], page=page)

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    event.reply.assert_called_with(
        "Could not locate the image by {} with image id {}.".format(username, image_id),
    )


@pytest.mark.asyncio
async def test_result_missing_between_pages(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        MockSubmission(post_id + 1, image_id=image_id + 16),
        MockSubmission(post_id, image_id=image_id + 3)
    ], page=1)
    neaten.api.with_user_folder(username, "gallery", [
        MockSubmission(post_id - 2, image_id=image_id - 27),
        MockSubmission(post_id - 3, image_id=image_id - 34)
    ], page=2)

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    event.reply.assert_called_with(
        "Could not locate the image by {} with image id {}.".format(username, image_id),
    )


@pytest.mark.asyncio
async def test_result_last_on_page(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        MockSubmission(post_id + 4, image_id=image_id + 16),
        MockSubmission(post_id + 3, image_id=image_id + 2),
        MockSubmission(post_id + 2, image_id=image_id + 1),
        submission
    ])

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    submission._send_message.assert_called_once()
    args, kwargs = submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_result_first_on_page(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        MockSubmission(post_id + 3, image_id=image_id + 16),
        MockSubmission(post_id + 2, image_id=image_id + 8)
    ], page=1)
    neaten.api.with_user_folder(username, "gallery", [
        submission,
        MockSubmission(post_id - 2, image_id=image_id - 2),
        MockSubmission(post_id - 7, image_id=image_id - 4),
        MockSubmission(post_id - 9, image_id=image_id - 10)
    ], page=2)

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    submission._send_message.assert_called_once()
    args, kwargs = submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
    assert kwargs['reply_to'] == event.message.id


@pytest.mark.asyncio
async def test_not_on_first_page_empty_second_page(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id)
    )
    neaten = NeatenFunctionality(MockExportAPI())
    neaten.api.with_user_folder(username, "gallery", [
        MockSubmission(post_id + 3, image_id=image_id + 16),
        MockSubmission(post_id + 2, image_id=image_id + 8)
    ], page=1)
    neaten.api.with_user_folder(username, "gallery", [
    ], page=2)

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    event.reply.assert_called_with(
        "Could not locate the image by {} with image id {}.".format(username, image_id),
    )


@pytest.mark.asyncio
async def test_result_in_scraps(mock_client):
    username = "fender"
    image_id = 1560331512
    post_id = 232347
    event = MockTelegramEvent.with_message(
        text="http://d.furaffinity.net/art/{0}/{1}/{1}.pic_of_me.png".format(username, image_id),
        client=mock_client,
    )
    submission = MockSubmission(post_id, image_id=image_id)
    neaten = NeatenFunctionality(MockExportAPI())
    for page in [1, 2]:
        neaten.api.with_user_folder(username, "gallery", [
            MockSubmission(post_id + 1 + (3 - page) * 5, image_id=image_id + 16 + (3 - page) * 56),
            MockSubmission(post_id + (3 - page) * 5, image_id=image_id + (3 - page) * 56),
            MockSubmission(post_id - 2 + (3 - page) * 5, image_id=image_id - 27 + (3 - page) * 56),
            MockSubmission(post_id - 3 + (3 - page) * 5, image_id=image_id - 34 + (3 - page) * 56)
        ], page=page)
    neaten.api.with_user_folder(username, "gallery", [], page=3)
    neaten.api.with_user_folder(username, "scraps", [
        MockSubmission(post_id + 1, image_id=image_id + 16),
        submission,
        MockSubmission(post_id - 2, image_id=image_id - 27),
        MockSubmission(post_id - 3, image_id=image_id - 34)
    ], page=1)

    with pytest.raises(StopPropagation):
        await neaten.call(event)

    submission._send_message.assert_called_once()
    args, kwargs = submission._send_message.call_args
    assert args[0] == mock_client
    assert args[1] == event.input_chat
    assert kwargs['reply_to'] == event.message.id
