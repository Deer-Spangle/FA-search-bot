import pytest
from telethon.events import StopPropagation
from telethon.tl.types import InputPhoto

from fa_search_bot.functionalities.inline_gallery import InlineGalleryFunctionality
from fa_search_bot.sites.furaffinity.fa_export_api import FAExportAPI
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.tests.functionality.inline.utils import assert_answer_is_error
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
from fa_search_bot.tests.util.mock_submission_cache import MockSubmissionCache
from fa_search_bot.tests.util.mock_telegram_event import MockTelegramEvent, _MockInlineBuilder


@pytest.mark.asyncio
async def test_user_gallery(mock_client):
    post_id1 = 234563
    post_id2 = 393282
    username = "fender"
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}")
    submission1 = MockSubmission(post_id1)
    submission2 = MockSubmission(post_id2)
    api = MockExportAPI().with_user_folder(username, "gallery", [submission1, submission2])
    cache = MockSubmissionCache()
    inline = InlineGalleryFunctionality(api, cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    assert event.answer.call_args.kwargs["next_offset"] == "2:0"
    assert event.answer.call_args.kwargs["gallery"] is True
    results = event.answer.call_args.args[0]
    assert isinstance(results, list)
    assert len(results) == 2
    assert isinstance(results[0], _MockInlineBuilder._MockInlinePhoto)
    assert isinstance(results[1], _MockInlineBuilder._MockInlinePhoto)
    assert results[0].kwargs["file"] == submission1.thumbnail_url
    assert results[0].kwargs["id"] == f"fa:{post_id1}"
    assert results[0].kwargs["text"] == submission1.link
    assert len(results[0].kwargs["buttons"]) == 1
    assert results[0].kwargs["buttons"][0].data == f"neaten_me:fa:{submission1.submission_id}".encode()
    assert results[1].kwargs["file"] == submission2.thumbnail_url
    assert results[1].kwargs["id"] == f"fa:{post_id2}"
    assert results[1].kwargs["text"] == submission2.link
    assert len(results[1].kwargs["buttons"]) == 1
    assert results[1].kwargs["buttons"][0].data == f"neaten_me:fa:{submission2.submission_id}".encode()


@pytest.mark.asyncio
async def test_user_gallery_short(mock_client):
    post_id1 = 234563
    post_id2 = 393282
    username = "fender"
    event = MockTelegramEvent.with_inline_query(query=f"g:{username}")
    submission1 = MockSubmission(post_id1)
    submission2 = MockSubmission(post_id2)
    api = MockExportAPI().with_user_folder(username, "gallery", [submission1, submission2])
    cache = MockSubmissionCache()
    inline = InlineGalleryFunctionality(api, cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    assert event.answer.call_args.kwargs["next_offset"] == "2:0"
    assert event.answer.call_args.kwargs["gallery"] is True
    results = event.answer.call_args.args[0]
    assert isinstance(results, list)
    assert len(results) == 2
    assert isinstance(results[0], _MockInlineBuilder._MockInlinePhoto)
    assert isinstance(results[1], _MockInlineBuilder._MockInlinePhoto)
    assert results[0].kwargs["file"] == submission1.thumbnail_url
    assert results[0].kwargs["id"] == f"fa:{post_id1}"
    assert results[0].kwargs["text"] == submission1.link
    assert len(results[0].kwargs["buttons"]) == 1
    assert results[0].kwargs["buttons"][0].data == f"neaten_me:fa:{submission1.submission_id}".encode()
    assert results[1].kwargs["file"] == submission2.thumbnail_url
    assert results[1].kwargs["id"] == f"fa:{post_id2}"
    assert results[1].kwargs["text"] == submission2.link
    assert len(results[1].kwargs["buttons"]) == 1
    assert results[1].kwargs["buttons"][0].data == f"neaten_me:fa:{submission2.submission_id}".encode()


@pytest.mark.asyncio
async def test_user_scraps(mock_client):
    post_id = 234563
    username = "citrinelle"
    event = MockTelegramEvent.with_inline_query(query=f"scraps:{username}")
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_folder(username, "scraps", [submission])
    cache = MockSubmissionCache()
    inline = InlineGalleryFunctionality(api, cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    results = event.answer.call_args.args[0]
    assert event.answer.call_args.kwargs["next_offset"] == "2:0"
    assert event.answer.call_args.kwargs["gallery"] is True
    assert isinstance(results, list)
    assert len(results) == 1
    assert isinstance(results[0], _MockInlineBuilder._MockInlinePhoto)
    assert results[0].kwargs["file"] == submission.thumbnail_url
    assert results[0].kwargs["id"] == f"fa:{post_id}"
    assert results[0].kwargs["text"] == submission.link
    assert len(results[0].kwargs["buttons"]) == 1
    assert results[0].kwargs["buttons"][0].data == f"neaten_me:fa:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_second_page(mock_client):
    post_id = 234563
    username = "citrinelle"
    event = MockTelegramEvent.with_inline_query(query=f"scraps:{username}", offset="2")
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_folder(username, "scraps", [submission], page=2)
    cache = MockSubmissionCache()
    inline = InlineGalleryFunctionality(api, cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    results = event.answer.call_args.args[0]
    assert event.answer.call_args.kwargs["next_offset"] == "3:0"
    assert event.answer.call_args.kwargs["gallery"] is True
    assert isinstance(results, list)
    assert len(results) == 1
    assert isinstance(results[0], _MockInlineBuilder._MockInlinePhoto)
    assert results[0].kwargs["file"] == submission.thumbnail_url
    assert results[0].kwargs["id"] == f"fa:{post_id}"
    assert results[0].kwargs["text"] == submission.link
    assert len(results[0].kwargs["buttons"]) == 1
    assert results[0].kwargs["buttons"][0].data == f"neaten_me:fa:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_empty_gallery(mock_client):
    username = "fender"
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}")
    api = MockExportAPI().with_user_folder(username, "gallery", [])
    cache = MockSubmissionCache()
    inline = InlineGalleryFunctionality(api, cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    assert_answer_is_error(
        event.answer,
        "Nothing in gallery.",
        f'There are no submissions in gallery for user "{username}".',
    )


@pytest.mark.asyncio
async def test_empty_scraps(mock_client):
    username = "fender"
    event = MockTelegramEvent.with_inline_query(query=f"scraps:{username}")
    api = MockExportAPI().with_user_folder(username, "scraps", [])
    cache = MockSubmissionCache()
    inline = InlineGalleryFunctionality(api, cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    assert_answer_is_error(
        event.answer,
        "Nothing in scraps.",
        f'There are no submissions in scraps for user "{username}".',
    )


@pytest.mark.asyncio
async def test_hypens_in_username(mock_client):
    post_id = 234563
    username = "dr-spangle"
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}")
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_folder(username, "gallery", [submission])
    cache = MockSubmissionCache()
    inline = InlineGalleryFunctionality(api, cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    results = event.answer.call_args.args[0]
    assert event.answer.call_args.kwargs["next_offset"] == "2:0"
    assert event.answer.call_args.kwargs["gallery"] is True
    assert isinstance(results, list)
    assert len(results) == 1
    assert isinstance(results[0], _MockInlineBuilder._MockInlinePhoto)
    assert results[0].kwargs["file"] == submission.thumbnail_url
    assert results[0].kwargs["id"] == f"fa:{post_id}"
    assert results[0].kwargs["text"] == submission.link
    assert len(results[0].kwargs["buttons"]) == 1
    assert results[0].kwargs["buttons"][0].data == f"neaten_me:fa:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_weird_characters_in_username(mock_client):
    post_id = 234563
    username = "l[i]s"
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}")
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_folder(username, "gallery", [submission])
    cache = MockSubmissionCache()
    inline = InlineGalleryFunctionality(api, cache)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    results = event.answer.call_args.args[0]
    assert event.answer.call_args.kwargs["next_offset"] == "2:0"
    assert event.answer.call_args.kwargs["gallery"] is True
    assert isinstance(results, list)
    assert len(results) == 1
    assert isinstance(results[0], _MockInlineBuilder._MockInlinePhoto)
    assert results[0].kwargs["file"] == submission.thumbnail_url
    assert results[0].kwargs["id"] == f"fa:{post_id}"
    assert results[0].kwargs["text"] == submission.link
    assert len(results[0].kwargs["buttons"]) == 1
    assert results[0].kwargs["buttons"][0].data == f"neaten_me:fa:{submission.submission_id}".encode()


@pytest.mark.asyncio
async def test_no_user_exists(requests_mock):
    username = "fakelad"
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}")
    # mock export api doesn't do non-existent users, so mocking with requests
    api = FAExportAPI("https://example.com", ignore_status=True)
    cache = MockSubmissionCache()
    inline = InlineGalleryFunctionality(api, cache)
    requests_mock.get(f"https://example.com/user/{username}/gallery.json", status_code=404)

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
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}")
    # mock export api doesn't do non-existent users, so mocking with requests
    api = FAExportAPI("https://example.com", ignore_status=True)
    cache = MockSubmissionCache()
    inline = InlineGalleryFunctionality(api, cache)
    requests_mock.get(f"https://example.com/user/{username}/gallery.json", status_code=404)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    assert_answer_is_error(
        event.answer,
        "User does not exist.",
        f'FurAffinity user does not exist by the name: "{username}".',
    )


@pytest.mark.asyncio
async def test_over_max_submissions(mock_client):
    username = "citrinelle"
    mock_api = MockExportAPI()
    cache = MockSubmissionCache()
    inline = InlineGalleryFunctionality(mock_api, cache)
    posts = inline.INLINE_MAX + 30
    post_ids = list(range(123456, 123456 + posts))
    submissions = [MockSubmission(x) for x in post_ids]
    mock_api.with_user_folder(username, "gallery", submissions)
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}")

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    results = event.answer.call_args.args[0]
    assert event.answer.call_args.kwargs["next_offset"] == f"1:{inline.INLINE_FRESH}"
    assert event.answer.call_args.kwargs["gallery"] is True
    assert isinstance(results, list)
    assert len(results) == inline.INLINE_FRESH
    assert isinstance(results[0], _MockInlineBuilder._MockInlinePhoto)
    assert isinstance(results[1], _MockInlineBuilder._MockInlinePhoto)
    for x in range(inline.INLINE_FRESH):
        assert results[x].kwargs["file"] == submissions[x].thumbnail_url
        assert results[x].kwargs["id"] == f"fa:{post_ids[x]}"
        assert results[x].kwargs["text"] == submissions[x].link
        assert len(results[x].kwargs["buttons"]) == 1
        assert results[x].kwargs["buttons"][0].data == f"neaten_me:fa:{submissions[x].submission_id}".encode()


@pytest.mark.asyncio
async def test_over_max_submissions_cached(mock_client):
    username = "citrinelle"
    mock_api = MockExportAPI()
    posts = InlineGalleryFunctionality.INLINE_MAX + 30
    post_ids = list(range(123456, 123456 + posts))
    sub_ids = [SubmissionID("fa", f"{post_id}") for post_id in post_ids]
    cache = MockSubmissionCache.with_submission_ids(sub_ids, username=username)
    inline = InlineGalleryFunctionality(mock_api, cache)
    submissions = [MockSubmission(x) for x in post_ids]
    mock_api.with_user_folder(username, "gallery", submissions)
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}")

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    results = event.answer.call_args.args[0]
    assert event.answer.call_args.kwargs["next_offset"] == f"1:{inline.INLINE_MAX}"
    assert event.answer.call_args.kwargs["gallery"] is True
    assert isinstance(results, list)
    assert len(results) == inline.INLINE_MAX
    assert isinstance(results[0], _MockInlineBuilder._MockInlinePhoto)
    assert isinstance(results[1], _MockInlineBuilder._MockInlinePhoto)
    for x in range(inline.INLINE_MAX):
        sent_sub = cache.load_cache(sub_ids[x])
        assert isinstance(results[x].kwargs["file"], InputPhoto)
        assert results[x].kwargs["file"].id == sent_sub.media_id
        assert results[x].kwargs["file"].access_hash == sent_sub.access_hash
        assert results[x].kwargs["id"] == f"fa:{post_ids[x]}"
        assert results[x].kwargs["text"] == submissions[x].link
        assert results[x].kwargs["buttons"] is None


@pytest.mark.asyncio
async def test_over_max_submissions_mix_cache(mock_client):
    username = "citrinelle"
    mock_api = MockExportAPI()
    num_posts = InlineGalleryFunctionality.INLINE_MAX + 30
    post_ids = list(range(123456, 123456 + num_posts))
    sub_ids = [SubmissionID("fa", f"{post_id}") for post_id in post_ids]
    cache_id_indexes = [0, 1, 2, 4, 7, 8]
    cache_sub_ids = [sub_ids[n] for n in cache_id_indexes]
    cache = MockSubmissionCache.with_submission_ids(cache_sub_ids, username=username)
    inline = InlineGalleryFunctionality(mock_api, cache)
    submissions = [MockSubmission(x) for x in post_ids]
    mock_api.with_user_folder(username, "gallery", submissions)
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}")

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    result_count = len(cache_id_indexes) + inline.INLINE_FRESH
    assert event.answer.call_args.kwargs["next_offset"] == f"1:{result_count}"
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
async def test_over_max_submissions_continue(mock_client):
    username = "citrinelle"
    posts = 3 * InlineGalleryFunctionality.INLINE_MAX
    post_ids = list(range(123456, 123456 + posts))
    submissions = [MockSubmission(x) for x in post_ids]
    api = MockExportAPI().with_user_folder(username, "gallery", submissions)
    cache = MockSubmissionCache()
    inline = InlineGalleryFunctionality(api, cache)
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}", offset=f"1:{inline.INLINE_FRESH}")

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    results = event.answer.call_args.args[0]
    assert event.answer.call_args.kwargs["next_offset"] == f"1:{2 * inline.INLINE_FRESH}"
    assert event.answer.call_args.kwargs["gallery"] is True
    assert isinstance(results, list)
    assert len(results) == inline.INLINE_FRESH
    assert isinstance(results[0], _MockInlineBuilder._MockInlinePhoto)
    assert isinstance(results[1], _MockInlineBuilder._MockInlinePhoto)
    for x in range(inline.INLINE_FRESH):
        assert results[x].kwargs["file"] == submissions[x + inline.INLINE_FRESH].thumbnail_url
        assert results[x].kwargs["id"] == f"fa:{post_ids[x + inline.INLINE_FRESH]}"
        assert results[x].kwargs["text"] == submissions[x + inline.INLINE_FRESH].link
        assert len(results[x].kwargs["buttons"]) == 1
        assert (
            results[x].kwargs["buttons"][0].data
            == f"neaten_me:fa:{submissions[x + inline.INLINE_FRESH].submission_id}".encode()
        )


@pytest.mark.asyncio
async def test_over_max_submissions_continue_end(mock_client):
    username = "citrinelle"
    posts = 72
    post_ids = list(range(123456, 123456 + posts))
    submissions = [MockSubmission(x) for x in post_ids]
    mock_api = MockExportAPI()
    mock_api.with_user_folder(username, "gallery", submissions)
    cache = MockSubmissionCache()
    inline = InlineGalleryFunctionality(mock_api, cache)
    skip = posts - inline.INLINE_FRESH + 3
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}", offset=f"1:{skip}")

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    results = event.answer.call_args.args[0]
    assert event.answer.call_args.kwargs["next_offset"] == "2:0"
    assert event.answer.call_args.kwargs["gallery"] is True
    assert isinstance(results, list)
    assert len(results) == inline.INLINE_FRESH - 3
    assert isinstance(results[0], _MockInlineBuilder._MockInlinePhoto)
    assert isinstance(results[1], _MockInlineBuilder._MockInlinePhoto)
    for x in range(inline.INLINE_FRESH - 3):
        assert results[x].kwargs["file"] == submissions[x + skip].thumbnail_url
        assert results[x].kwargs["id"] == f"fa:{post_ids[x + skip]}"
        assert results[x].kwargs["text"] == submissions[x + skip].link
        assert len(results[x].kwargs["buttons"]) == 1
        assert results[x].kwargs["buttons"][0].data == f"neaten_me:fa:{submissions[x + skip].submission_id}".encode()


@pytest.mark.asyncio
async def test_over_max_submissions_continue_over_page(mock_client):
    username = "citrinelle"
    page_1_count = 72
    page_1_ids = list(range(123456, 123456 + page_1_count))
    page_1_max = max(page_1_ids)
    page_2_count = 25
    page_2_ids = list(range(page_1_max, page_1_max + page_2_count))
    page_1_submissions = [MockSubmission(x) for x in page_1_ids]
    page_2_submissions = [MockSubmission(x) for x in page_2_ids]
    skip = page_1_count + 5
    api = MockExportAPI()\
        .with_user_folder(username, "gallery", page_1_submissions, page=1)\
        .with_user_folder(username, "gallery", page_2_submissions, page=2)
    cache = MockSubmissionCache()
    inline = InlineGalleryFunctionality(api, cache)
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}", offset=f"1:{skip}")

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    results = event.answer.call_args.args[0]
    assert event.answer.call_args.kwargs["next_offset"] == "2:5"
    assert event.answer.call_args.kwargs["gallery"] is True
    assert isinstance(results, list)
    assert len(results) == 5
    for n, result in enumerate(results):
        assert result.kwargs["file"] == page_2_submissions[n].thumbnail_url
        assert result.kwargs["id"] == f"fa:{page_2_ids[n]}"
        assert result.kwargs["text"] == page_2_submissions[n].link
        assert len(result.kwargs["buttons"]) == 1
        assert result.kwargs["buttons"][0].data == f"neaten_me:fa:{page_2_submissions[n].submission_id}".encode()


@pytest.mark.asyncio
async def test_no_username_set(requests_mock):
    username = ""
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}")
    # mock export api doesn't do non-existent users, so mocking with requests
    api = FAExportAPI("https://example.com", ignore_status=True)
    cache = MockSubmissionCache()
    inline = InlineGalleryFunctionality(api, cache)
    requests_mock.get(
        f"https://example.com/user/{username}/gallery.json?page=1&full=1",
        json={
            "id": None,
            "name": "gallery",
            "profile": "https://www.furaffinity.net/user/gallery/",
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
