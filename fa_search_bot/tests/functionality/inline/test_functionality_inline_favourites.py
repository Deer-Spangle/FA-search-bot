import pytest
from telethon.events import StopPropagation
from telethon.tl.types import InputPhoto

from fa_search_bot.functionalities.inline_favs import InlineFavsFunctionality
from fa_search_bot.sites.furaffinity.fa_export_api import FAExportAPI
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.tests.functionality.inline.utils import assert_answer_is_error
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_submission_cache import MockSubmissionCache
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
    cache = MockSubmissionCache()
    inline = InlineFavsFunctionality(api, cache)

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
    assert args[0][0].kwargs["id"] == f"fa:{post_id1}"
    assert args[0][0].kwargs["text"] == submission1.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:fa:{submission1.submission_id}".encode()
    assert args[0][1].kwargs["file"] == submission2.thumbnail_url
    assert args[0][1].kwargs["id"] == f"fa:{post_id2}"
    assert args[0][1].kwargs["text"] == submission2.link
    assert len(args[0][1].kwargs["buttons"]) == 1
    assert args[0][1].kwargs["buttons"][0].data == f"neaten_me:fa:{submission2.submission_id}".encode()


@pytest.mark.asyncio
async def test_user_favs(mock_client):
    post_id = 234563
    username = "citrinelle"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_favs(username, [submission])
    cache = MockSubmissionCache()
    inline = InlineFavsFunctionality(api, cache)

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
    assert args[0][0].kwargs["id"] == f"fa:{post_id}"
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:fa:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_american_spelling(mock_client):
    post_id = 234563
    username = "citrinelle"
    event = MockTelegramEvent.with_inline_query(query=f"favorites:{username}")
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_favs(username, [submission])
    cache = MockSubmissionCache()
    inline = InlineFavsFunctionality(api, cache)

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
    assert args[0][0].kwargs["id"] == f"fa:{post_id}"
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:fa:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_continue_from_fav_id(mock_client):
    post_id = 234563
    fav_id = "354233"
    username = "citrinelle"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}", offset=fav_id)
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_favs(username, [submission], next_id=fav_id)
    cache = MockSubmissionCache()
    inline = InlineFavsFunctionality(api, cache)

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
    assert args[0][0].kwargs["id"] == f"fa:{post_id}"
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:fa:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_empty_favs(mock_client):
    username = "fender"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    api = MockExportAPI().with_user_favs(username, [])
    cache = MockSubmissionCache()
    inline = InlineFavsFunctionality(api, cache)

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
    cache = MockSubmissionCache()
    inline = InlineFavsFunctionality(api, cache)

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
    assert args[0][0].kwargs["id"] == f"fa:{post_id}"
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:fa:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_weird_characters_in_username(mock_client):
    post_id = 234563
    username = "l[i]s"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_favs(username, [submission])
    cache = MockSubmissionCache()
    inline = InlineFavsFunctionality(api, cache)

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
    assert args[0][0].kwargs["id"] == f"fa:{post_id}"
    assert args[0][0].kwargs["text"] == submission.link
    assert len(args[0][0].kwargs["buttons"]) == 1
    assert args[0][0].kwargs["buttons"][0].data == f"neaten_me:fa:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_no_user_exists(requests_mock):
    username = "fakelad"
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    # mock export api doesn't do non-existent users, so mocking with requests
    api = FAExportAPI("https://example.com", ignore_status=True)
    cache = MockSubmissionCache()
    inline = InlineFavsFunctionality(api, cache)
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
    cache = MockSubmissionCache()
    inline = InlineFavsFunctionality(api, cache)
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
    cache = MockSubmissionCache()
    inline = InlineFavsFunctionality(api, cache)
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == submissions[inline.INLINE_FRESH - 1].fav_id
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == inline.INLINE_FRESH
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert isinstance(args[0][1], _MockInlineBuilder._MockInlinePhoto)
    for x in range(inline.INLINE_FRESH):
        assert args[0][x].kwargs["file"] == submissions[x].thumbnail_url
        assert args[0][x].kwargs["id"] == f"fa:{post_ids[x]}"
        assert args[0][x].kwargs["text"] == submissions[x].link
        assert len(args[0][x].kwargs["buttons"]) == 1
        assert args[0][x].kwargs["buttons"][0].data == f"neaten_me:fa:{submissions[x].submission_id}".encode()


@pytest.mark.asyncio
async def test_over_max_favs_cached(mock_client):
    username = "citrinelle"
    post_ids = list(range(123456, 123456 + 72))
    submissions = [MockSubmission(x) for x in post_ids]
    api = MockExportAPI().with_user_favs(username, submissions)
    sub_ids = [SubmissionID("fa", f"{x}") for x in post_ids]
    cache = MockSubmissionCache.with_submission_ids(sub_ids)
    inline = InlineFavsFunctionality(api, cache)
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
        sent_sub = cache.load_cache(sub_ids[x])
        assert isinstance(args[0][x].kwargs["file"], InputPhoto)
        assert args[0][x].kwargs["file"].id == sent_sub.media_id
        assert args[0][x].kwargs["file"].access_hash == sent_sub.access_hash
        assert args[0][x].kwargs["id"] == f"fa:{post_ids[x]}"
        assert args[0][x].kwargs["text"] == submissions[x].link
        assert args[0][x].kwargs["buttons"] is None


@pytest.mark.asyncio
async def test_over_max_favs_mix_cache(mock_client):
    username = "citrinelle"
    post_ids = list(range(123456, 123456 + 72))
    submissions = [MockSubmission(x) for x in post_ids]
    api = MockExportAPI().with_user_favs(username, submissions)
    sub_ids = [SubmissionID("fa", f"{x}") for x in post_ids]
    cache_id_indexes = [0, 1, 3, 4, 5, 8]
    cache_sub_ids = [sub_ids[n] for n in cache_id_indexes]
    cache = MockSubmissionCache.with_submission_ids(cache_sub_ids)
    inline = InlineFavsFunctionality(api, cache)
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    result_count = len(cache_id_indexes) + inline.INLINE_FRESH
    assert event.answer.call_args.kwargs["next_offset"] == submissions[result_count - 1].fav_id
    assert event.answer.call_args.kwargs["gallery"] is True
    results = event.answer.call_args.args[0]
    assert isinstance(results, list)
    assert len(results) == result_count
    assert isinstance(results[0], _MockInlineBuilder._MockInlinePhoto)
    assert isinstance(results[1], _MockInlineBuilder._MockInlinePhoto)
    for n, result in enumerate(results):
        if n in cache_id_indexes:
            sent_sub = cache.load_cache(sub_ids[n])
            assert isinstance(result.kwargs["file"], InputPhoto)
            assert result.kwargs["file"].id == sent_sub.media_id
            assert result.kwargs["file"].access_hash == sent_sub.access_hash
            assert result.kwargs["id"] == sub_ids[n].to_inline_code()
            assert result.kwargs["text"] == submissions[n].link
            assert result.kwargs["buttons"] is None
        else:
            assert result.kwargs["file"] == submissions[n].thumbnail_url
            assert result.kwargs["id"] == sub_ids[n].to_inline_code()
            assert result.kwargs["text"] == submissions[n].link
            assert len(result.kwargs["buttons"]) == 1
            assert result.kwargs["buttons"][0].data == f"neaten_me:{sub_ids[n].to_inline_code()}".encode()


@pytest.mark.asyncio
async def test_no_username_set(requests_mock):
    username = ""
    event = MockTelegramEvent.with_inline_query(query=f"favs:{username}")
    # mock export api doesn't do non-existent users, so mocking with requests
    api = FAExportAPI("https://example.com", ignore_status=True)
    cache = MockSubmissionCache()
    inline = InlineFavsFunctionality(api, cache)
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
    cache = MockSubmissionCache()
    inline = InlineFavsFunctionality(api, cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] is None
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 0
