import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.inline_favs import InlineFavsFunctionality
from fa_search_bot.sites.fa_export_api import FAExportAPI
from fa_search_bot.tests.functionality.inline.utils import assert_answer_is_error
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
    api = MockExportAPI().with_user_favs(username, [submission1, submission2])
    inline = InlineFavsFunctionality(api)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == submission2.fav_id
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 2
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert isinstance(args[0][1], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs["file"] == submission1.thumbnail_url
    assert args[0][0].kwargs["id"] == str(post_id1)
    assert args[0][0].kwargs["text"] == submission1.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:{submission1.submission_id}".encode()
    assert args[0][1].kwargs["file"] == submission2.thumbnail_url
    assert args[0][1].kwargs["id"] == str(post_id2)
    assert args[0][1].kwargs["text"] == submission2.link
    assert len(args[0][1].kwargs["buttons"]) == 1
    assert args[0][1].kwargs["buttons"][0].data == f"neaten_me:{submission2.submission_id}".encode()


@pytest.mark.asyncio
async def test_user_favs(mock_client):
    post_id = 234563
    username = "citrinelle"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_favs(username, [submission])
    inline = InlineFavsFunctionality(api)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == submission.fav_id
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs["file"] == submission.thumbnail_url
    assert args[0][0].kwargs["id"] == str(post_id)
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_american_spelling(mock_client):
    post_id = 234563
    username = "citrinelle"
    event = MockTelegramEvent.with_inline_query(query=f"favorites:{username}")
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_favs(username, [submission])
    inline = InlineFavsFunctionality(api)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == submission.fav_id
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs["file"] == submission.thumbnail_url
    assert args[0][0].kwargs["id"] == str(post_id)
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_continue_from_fav_id(mock_client):
    post_id = 234563
    fav_id = "354233"
    username = "citrinelle"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}", offset=fav_id)
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_favs(username, [submission], next_id=fav_id)
    inline = InlineFavsFunctionality(api)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == submission.fav_id
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs["file"] == submission.thumbnail_url
    assert args[0][0].kwargs["id"] == str(post_id)
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_empty_favs(mock_client):
    username = "fender"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    api = MockExportAPI().with_user_favs(username, [])
    inline = InlineFavsFunctionality(api)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    assert_answer_is_error(
        event.answer,
        "Nothing in favourites.",
        f'There are no favourites for user "{username}".',
    )


@pytest.mark.asyncio
async def test_hypens_in_username(mock_client):
    post_id = 234563
    username = "dr-spangle"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_favs(username, [submission])
    inline = InlineFavsFunctionality(api)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == submission.fav_id
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs["file"] == submission.thumbnail_url
    assert args[0][0].kwargs["id"] == str(post_id)
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_weird_characters_in_username(mock_client):
    post_id = 234563
    username = "l[i]s"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_favs(username, [submission])
    inline = InlineFavsFunctionality(api)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == submission.fav_id
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 1
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert args[0][0].kwargs["file"] == submission.thumbnail_url
    assert args[0][0].kwargs["id"] == str(post_id)
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_no_user_exists(requests_mock):
    username = "fakelad"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    # mock export api doesn't do non-existent users, so mocking with requests
    api = FAExportAPI("https://example.com", ignore_status=True)
    inline = InlineFavsFunctionality(api)
    requests_mock.get(f"https://example.com/user/{username}/favorites.json", status_code=404)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    assert_answer_is_error(
        event.answer,
        "User does not exist.",
        f'FurAffinity user does not exist by the name: "{username}".',
    )


@pytest.mark.asyncio
async def test_username_with_colon(requests_mock):
    # FA doesn't allow usernames to have : in them
    username = "fake:lad"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    # mock export api doesn't do non-existent users, so mocking with requests
    api = FAExportAPI("https://example.com", ignore_status=True)
    inline = InlineFavsFunctionality(api)
    requests_mock.get(f"https://example.com/user/{username}/favorites.json", status_code=404)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    assert_answer_is_error(
        event.answer,
        "User does not exist.",
        f'FurAffinity user does not exist by the name: "{username}".',
    )


@pytest.mark.asyncio
async def test_over_max_favs(mock_client):
    username = "citrinelle"
    post_ids = list(range(123456, 123456 + 72))
    submissions = [MockSubmission(x) for x in post_ids]
    api = MockExportAPI().with_user_favs(username, submissions)
    inline = InlineFavsFunctionality(api)
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == submissions[inline.INLINE_MAX - 1].fav_id
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == inline.INLINE_MAX
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert isinstance(args[0][1], _MockInlineBuilder._MockInlinePhoto)
    for x in range(inline.INLINE_MAX):
        assert args[0][x].kwargs["file"] == submissions[x].thumbnail_url
        assert args[0][x].kwargs["id"] == str(post_ids[x])
        assert args[0][x].kwargs["text"] == submissions[x].link
        assert len(args[0][x].kwargs["buttons"]) == 1
        assert args[0][x].kwargs["buttons"][0].data == f"neaten_me:{submissions[x].submission_id}".encode()


@pytest.mark.asyncio
async def test_no_username_set(requests_mock):
    username = ""
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    # mock export api doesn't do non-existent users, so mocking with requests
    api = FAExportAPI("https://example.com", ignore_status=True)
    inline = InlineFavsFunctionality(api)
    requests_mock.get(
        f"https://example.com/user/{username}/favorites.json?page=1&full=1",
        json={
            "id": None,
            "name": "favorites",
            "profile": "https://www.furaffinity.net/user/favorites/",
        },
    )

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    assert_answer_is_error(
        event.answer,
        "User does not exist.",
        f'FurAffinity user does not exist by the name: "{username}".',
    )


@pytest.mark.asyncio
async def test_user_favourites_last_page(mock_client):
    # On the last page of favourites, if you specify "next", it repeats the same page, this simulates that.
    post_id1 = 234563
    post_id2 = 393282
    submission1 = MockSubmission(post_id1)
    submission2 = MockSubmission(post_id2)
    username = "fender"
    event = MockTelegramEvent.with_inline_query(query=f"favourites:{username}", offset=submission2.fav_id)
    api = MockExportAPI().with_user_favs(username, [submission1, submission2], next_id=submission2.fav_id)
    inline = InlineFavsFunctionality(api)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] is None
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 0
