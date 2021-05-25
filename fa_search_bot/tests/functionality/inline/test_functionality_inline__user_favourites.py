import pytest
from telegram import InputMessageContent
from telethon.events import StopPropagation

from fa_search_bot.fa_export_api import FAExportAPI
from fa_search_bot.functionalities.inline import InlineFunctionality
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent, _MockInlineBuilder


@pytest.mark.asyncio
async def test_user_favourites(mock_client):
    post_id1 = 234563
    post_id2 = 393282
    username = "fender"
    event = MockTelegramEvent.with_inline_query(query=f"favourites:{username}")
    submission1 = MockSubmission(post_id1)
    submission2 = MockSubmission(post_id2)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [submission1, submission2])

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] == submission2.fav_id
    assert isinstance(args[0], list)
    assert len(args[0]) == 2
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert isinstance(args[0][1], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs == {
        "id": str(post_id1),
        "file": submission1.thumbnail_url,
        "text": submission1.link,
    }
    assert args[0][1].kwargs == {
        "id": str(post_id2),
        "file": submission2.thumbnail_url,
        "text": submission2.link,
    }


@pytest.mark.asyncio
async def test_user_favs(mock_client):
    post_id = 234563
    username = "citrinelle"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [submission])

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] == submission.fav_id
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs == {
        "id": str(post_id),
        "file": submission.thumbnail_url,
        "text": submission.link
    }


@pytest.mark.asyncio
async def test_american_spelling(mock_client):
    post_id = 234563
    username = "citrinelle"
    event = MockTelegramEvent.with_inline_query(query=f"favorites:{username}")
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [submission])

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] == submission.fav_id
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs == {
        "id": str(post_id),
        "file": submission.thumbnail_url,
        "text": submission.link
    }


@pytest.mark.asyncio
async def test_continue_from_fav_id(mock_client):
    post_id = 234563
    fav_id = "354233"
    username = "citrinelle"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}", offset=fav_id)
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [submission], next_id=fav_id)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] == submission.fav_id
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs == {
        "id": str(post_id),
        "file": submission.thumbnail_url,
        "text": submission.link
    }


@pytest.mark.asyncio
async def test_empty_favs(mock_client):
    username = "fender"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [])

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] is None
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlineArticle)
    assert args[0][0].kwargs == {
        "title": "Nothing in favourites.",
        "description": f"There are no favourites for user \"{username}\"."
    }


@pytest.mark.asyncio
async def test_hypens_in_username(mock_client):
    post_id = 234563
    username = "dr-spangle"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [submission])

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] == submission.fav_id
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs == {
        "id": str(post_id),
        "file": submission.thumbnail_url,
        "text": submission.link
    }


@pytest.mark.asyncio
async def test_weird_characters_in_username(mock_client):
    post_id = 234563
    username = "l[i]s"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    submission = MockSubmission(post_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [submission])

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] == submission.fav_id
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs == {
        "id": str(post_id),
        "file": submission.thumbnail_url,
        "text": submission.link
    }


@pytest.mark.asyncio
async def test_no_user_exists(context, requests_mock):
    username = "fakelad"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    inline = InlineFunctionality(MockExportAPI())
    # mock export api doesn't do non-existent users, so mocking with requests
    inline.api = FAExportAPI("http://example.com", ignore_status=True)
    requests_mock.get(
        f"http://example.com/user/{username}/favorites.json",
        status_code=404
    )

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] is None
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlineArticle)
    assert args[0][0].kwargs == {
        "title": "User does not exist.",
        "description": f"FurAffinity user does not exist by the name: \"{username}\"."
    }


@pytest.mark.asyncio
async def test_username_with_colon(context, requests_mock):
    # FA doesn't allow usernames to have : in them
    username = "fake:lad"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    inline = InlineFunctionality(MockExportAPI())
    # mock export api doesn't do non-existent users, so mocking with requests
    inline.api = FAExportAPI("http://example.com", ignore_status=True)
    requests_mock.get(
        f"http://example.com/user/{username}/favorites.json",
        status_code=404
    )

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] is None
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlineArticle)
    assert args[0][0].kwargs == {
        "title": "User does not exist.",
        "description": f"FurAffinity user does not exist by the name: \"{username}\"."
    }


@pytest.mark.asyncio
async def test_over_48_favs(mock_client):
    username = "citrinelle"
    post_ids = list(range(123456, 123456 + 72))
    submissions = [MockSubmission(x) for x in post_ids]
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, submissions)
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] == submissions[47].fav_id
    assert isinstance(args[0], list)
    assert len(args[0]) == 48
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert isinstance(args[0][1], _MockInlineBuilder._MockInlinePhoto)
    for x in range(48):
        assert args[0][x].kwargs == {
            "id": str(post_ids[x]),
            "file": submissions[x].thumbnail_url,
            "text": submissions[x].link
        }


@pytest.mark.asyncio
async def test_no_username_set(context, requests_mock):
    username = ""
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    inline = InlineFunctionality(MockExportAPI())
    # mock export api doesn't do non-existent users, so mocking with requests
    inline.api = FAExportAPI("http://example.com", ignore_status=True)
    requests_mock.get(
        f"http://example.com/user/{username}/favorites.json?page=1&full=1",
        json={
            "id": None,
            "name": "favorites",
            "profile": "https://www.furaffinity.net/user/favorites/"
        }
    )

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] is None
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlineArticle)
    assert args[0][0].kwargs == {
        "title": "User does not exist.",
        "description": f"FurAffinity user does not exist by the name: \"{username}\"."
    }


@pytest.mark.asyncio
async def test_user_favourites_last_page(mock_client):
    # On the last page of favourites, if you specify "next", it repeats the same page, this simulates that.
    post_id1 = 234563
    post_id2 = 393282
    submission1 = MockSubmission(post_id1)
    submission2 = MockSubmission(post_id2)
    username = "fender"
    event = MockTelegramEvent.with_inline_query(query=f"favourites:{username}", offset=submission2.fav_id)
    inline = InlineFunctionality(MockExportAPI())
    inline.api.with_user_favs(username, [submission1, submission2], next_id=submission2.fav_id)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]['next_offset'] is None
    assert isinstance(args[0], list)
    assert len(args[0]) == 0
