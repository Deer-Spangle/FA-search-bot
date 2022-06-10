from unittest import mock

import pytest

from fa_search_bot.sites.fa_handler import FAHandler
from fa_search_bot.sites.site_handler import HandlerException
from fa_search_bot.tests.conftest import MockChat
from fa_search_bot.tests.util.mock_export_api import MockExportAPI
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder


def test_site_name_and_code():
    handler = FAHandler(MockExportAPI())

    assert handler.site_code == "fa"
    assert isinstance(handler.site_name, str)


def test_find_links_in_str():
    handler = FAHandler(MockExportAPI())
    submission = SubmissionBuilder().build_full_submission()
    haystack = f"Hello there\n{submission.link}, thing {submission.thumbnail_url} oh and {submission.download_url}"

    results = handler.find_links_in_str(haystack)

    assert len(results) == 3
    assert any(result in submission.link for result in results)
    assert any(result in submission.thumbnail_url for result in results)
    assert any(result in submission.download_url for result in results)


@pytest.mark.asyncio
async def test_get_submission_id_from_link__sub_link():
    handler = FAHandler(MockExportAPI())
    submission = SubmissionBuilder().build_full_submission()
    link = handler.find_links_in_str(submission.link)[0]

    result = await handler.get_submission_id_from_link(link)

    assert str(result) == submission.submission_id


@pytest.mark.asyncio
async def test_get_submission_id_from_link__thumb_link():
    handler = FAHandler(MockExportAPI())
    submission = SubmissionBuilder().build_full_submission()
    link = handler.find_links_in_str(submission.thumbnail_url)[0]

    result = await handler.get_submission_id_from_link(link)

    assert str(result) == submission.submission_id


@pytest.mark.asyncio
async def test_get_submission_id_from_link__direct_link():
    username = "fender"
    submission = SubmissionBuilder(username=username).build_full_submission()
    api = MockExportAPI().with_user_folder(username, "gallery", [submission])
    handler = FAHandler(api)
    link = handler.find_links_in_str(submission.download_url)[0]

    result = await handler.get_submission_id_from_link(link)

    assert str(result) == submission.submission_id


@pytest.mark.asyncio
async def test_get_submission_id_from_link__direct_link_empty_gallery():
    username = "fender"
    submission = SubmissionBuilder(username=username).build_full_submission()
    api = MockExportAPI().with_user_folder(username, "gallery", [])
    handler = FAHandler(api)
    link = handler.find_links_in_str(submission.download_url)[0]

    with pytest.raises(HandlerException):
        await handler.get_submission_id_from_link(link)


@pytest.mark.asyncio
async def test_get_submission_id_from_link__direct_link_no_match():
    username = "fender"
    submission = SubmissionBuilder(username=username).build_full_submission()
    others = [SubmissionBuilder(username=username).build_full_submission() for _ in range(10)]
    api = MockExportAPI().with_user_folder(username, "gallery", others)
    handler = FAHandler(api)
    link = handler.find_links_in_str(submission.download_url)[0]

    with pytest.raises(HandlerException):
        await handler.get_submission_id_from_link(link)


@pytest.mark.asyncio
async def test_get_submission_id_from_link__no_link():
    handler = FAHandler(MockExportAPI())

    result = await handler.get_submission_id_from_link("hello world")

    assert result is None


@pytest.mark.asyncio
async def test_send_submission(mock_client):
    submission = SubmissionBuilder().build_full_submission()
    handler = FAHandler(MockExportAPI().with_submission(submission))
    chat = MockChat(12345)
    reply_to = 64343
    prefix = "Some prefix"

    with mock.patch("fa_search_bot.sites.sendable.Sendable.send_message") as mock_send:
        await handler.send_submission(
            submission.submission_id,
            mock_client,
            chat,
            reply_to=reply_to,
            prefix=prefix,
            edit=True,
        )

    mock_send.assert_called_once()
    assert mock_send.call_args.args == (mock_client, chat)
    assert mock_send.call_args.kwargs["reply_to"] == reply_to
    assert mock_send.call_args.kwargs["prefix"] == prefix
    assert mock_send.call_args.kwargs["edit"] is True
