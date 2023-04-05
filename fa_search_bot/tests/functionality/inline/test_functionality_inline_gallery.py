import pytest
from telethon.events import StopPropagation

from fa_search_bot.functionalities.inline_gallery import InlineGalleryFunctionality
from fa_search_bot.sites.furaffinity.fa_export_api import FAExportAPI
from fa_search_bot.tests.functionality.inline.utils import assert_answer_is_error
from fa_search_bot.tests.util.mock_export_api import MockExportAPI, MockSubmission
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
    inline = InlineGalleryFunctionality(api)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2"
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
async def test_user_gallery_short(mock_client):
    post_id1 = 234563
    post_id2 = 393282
    username = "fender"
    event = MockTelegramEvent.with_inline_query(query=f"g:{username}")
    submission1 = MockSubmission(post_id1)
    submission2 = MockSubmission(post_id2)
    api = MockExportAPI().with_user_folder(username, "gallery", [submission1, submission2])
    inline = InlineGalleryFunctionality(api)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2"
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
async def test_user_scraps(mock_client):
    post_id = 234563
    username = "citrinelle"
    event = MockTelegramEvent.with_inline_query(query=f"scraps:{username}")
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_folder(username, "scraps", [submission])
    inline = InlineGalleryFunctionality(api)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2"
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
async def test_second_page(mock_client):
    post_id = 234563
    username = "citrinelle"
    event = MockTelegramEvent.with_inline_query(query=f"scraps:{username}", offset="2")
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_folder(username, "scraps", [submission], page=2)
    inline = InlineGalleryFunctionality(api)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "3"
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
async def test_empty_gallery(mock_client):
    username = "fender"
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}")
    api = MockExportAPI().with_user_folder(username, "gallery", [])
    inline = InlineGalleryFunctionality(api)

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
    inline = InlineGalleryFunctionality(api)

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
    inline = InlineGalleryFunctionality(api)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2"
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
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}")
    submission = MockSubmission(post_id)
    api = MockExportAPI().with_user_folder(username, "gallery", [submission])
    inline = InlineGalleryFunctionality(api)

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2"
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
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}")
    # mock export api doesn't do non-existent users, so mocking with requests
    api = FAExportAPI("https://example.com", ignore_status=True)
    inline = InlineGalleryFunctionality(api)
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
    inline = InlineGalleryFunctionality(api)
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
    inline = InlineGalleryFunctionality(mock_api)
    posts = inline.INLINE_MAX + 30
    post_ids = list(range(123456, 123456 + posts))
    submissions = [MockSubmission(x) for x in post_ids]
    mock_api.with_user_folder(username, "gallery", submissions)
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}")

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == f"1:{inline.INLINE_MAX}"
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
async def test_over_max_submissions_continue(mock_client):
    username = "citrinelle"
    posts = 3 * InlineGalleryFunctionality.INLINE_MAX
    post_ids = list(range(123456, 123456 + posts))
    submissions = [MockSubmission(x) for x in post_ids]
    api = MockExportAPI().with_user_folder(username, "gallery", submissions)
    inline = InlineGalleryFunctionality(api)
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}", offset=f"1:{inline.INLINE_MAX}")

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == f"1:{2 * inline.INLINE_MAX}"
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == inline.INLINE_MAX
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert isinstance(args[0][1], _MockInlineBuilder._MockInlinePhoto)
    for x in range(inline.INLINE_MAX):
        assert args[0][x].kwargs["file"] == submissions[x + inline.INLINE_MAX].thumbnail_url
        assert args[0][x].kwargs["id"] == str(post_ids[x + inline.INLINE_MAX])
        assert args[0][x].kwargs["text"] == submissions[x + inline.INLINE_MAX].link
        assert len(args[0][x].kwargs["buttons"]) == 1
        assert (
            args[0][x].kwargs["buttons"][0].data
            == f"neaten_me:{submissions[x + inline.INLINE_MAX].submission_id}".encode()
        )


@pytest.mark.asyncio
async def test_over_max_submissions_continue_end(mock_client):
    username = "citrinelle"
    posts = 72
    post_ids = list(range(123456, 123456 + posts))
    submissions = [MockSubmission(x) for x in post_ids]
    mock_api = MockExportAPI()
    mock_api.with_user_folder(username, "gallery", submissions)
    inline = InlineGalleryFunctionality(mock_api)
    skip = posts - inline.INLINE_MAX + 3
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}", offset=f"1:{skip}")

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2"
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == inline.INLINE_MAX - 3
    assert isinstance(args[0][0], _MockInlineBuilder._MockInlinePhoto)
    assert isinstance(args[0][1], _MockInlineBuilder._MockInlinePhoto)
    for x in range(inline.INLINE_MAX - 3):
        assert args[0][x].kwargs["file"] == submissions[x + skip].thumbnail_url
        assert args[0][x].kwargs["id"] == str(post_ids[x + skip])
        assert args[0][x].kwargs["text"] == submissions[x + skip].link
        assert len(args[0][x].kwargs["buttons"]) == 1
        assert args[0][x].kwargs["buttons"][0].data == f"neaten_me:{submissions[x + skip].submission_id}".encode()


@pytest.mark.asyncio
async def test_over_max_submissions_continue_over_page(mock_client):
    username = "citrinelle"
    posts = 72
    post_ids = list(range(123456, 123456 + posts))
    skip = posts + 5
    submissions = [MockSubmission(x) for x in post_ids]
    api = MockExportAPI().with_user_folder(username, "gallery", submissions)
    inline = InlineGalleryFunctionality(api)
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}", offset=f"1:{skip}")

    with pytest.raises(StopPropagation):
        await inline.call(event)

    event.answer.assert_called_once()
    args = event.answer.call_args[0]
    assert event.answer.call_args[1]["next_offset"] == "2"
    assert event.answer.call_args[1]["gallery"] is True
    assert isinstance(args[0], list)
    assert len(args[0]) == 0


@pytest.mark.asyncio
async def test_no_username_set(requests_mock):
    username = ""
    event = MockTelegramEvent.with_inline_query(query=f"gallery:{username}")
    # mock export api doesn't do non-existent users, so mocking with requests
    api = FAExportAPI("https://example.com", ignore_status=True)
    inline = InlineGalleryFunctionality(api)
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
