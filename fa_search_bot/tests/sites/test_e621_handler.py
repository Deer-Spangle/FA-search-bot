import asyncio
from unittest import mock
from unittest.mock import Mock

import pytest
from telethon.tl.custom import InlineBuilder

from fa_search_bot.sites.e621.e621_handler import E621Handler
from fa_search_bot.sites.site_handler import HandlerException
from fa_search_bot.sites.site_link import SiteLink
from fa_search_bot.sites.submission_id import SubmissionID
from fa_search_bot.tests.conftest import MockChat
from fa_search_bot.tests.util.mock_e621_client import MockAsyncYippiClient, MockPost


def async_return(result):
    f = asyncio.Future()
    f.set_result(result)
    return f


def test_site_name_and_code():
    api = MockAsyncYippiClient()
    handler = E621Handler(api)

    assert handler.site_code == "e6"
    assert isinstance(handler.site_name, str)


def test_find_links_in_str():
    post_id = 164532
    post = MockPost(post_id=post_id)
    handler = E621Handler(MockAsyncYippiClient())
    haystack = f"Hello there\n{post._post_link}, thing {post._post_link_old} oh and {post._direct_link}"

    results = handler.find_links_in_str(haystack)

    assert len(results) == 3
    assert any(result.link in post._post_link for result in results)
    assert any(result.link in post._post_link_old for result in results)
    assert any(result.link in post._direct_link for result in results)


def test_find_safe_links_in_str():
    post_id = 164532
    post = MockPost(post_id=post_id)
    handler = E621Handler(MockAsyncYippiClient())
    haystack = f"Hello there\n{post._post_link_safe}, thing {post._post_link_old_safe} oh and {post._direct_link_safe}"

    results = handler.find_links_in_str(haystack)

    assert len(results) == 3
    assert any(result.link in post._post_link_safe for result in results)
    assert any(result.link in post._post_link_old_safe for result in results)
    assert any(result.link in post._direct_link_safe for result in results)


@pytest.mark.asyncio
async def test_get_submission_id_from_link__post_link():
    post_id = 34433
    post = MockPost(post_id=post_id)
    api = MockAsyncYippiClient([post])
    handler = E621Handler(api)
    link = handler.find_links_in_str(post._post_link)[0]

    result = await handler.get_submission_id_from_link(link)

    assert result.submission_id == str(post_id)


@pytest.mark.asyncio
async def test_get_submission_id_from_link__safe_post_link():
    post_id = 34433
    post = MockPost(post_id=post_id)
    api = MockAsyncYippiClient([post])
    handler = E621Handler(api)
    link = handler.find_links_in_str(post._post_link_safe)[0]

    result = await handler.get_submission_id_from_link(link)

    assert result.submission_id == str(post_id)


@pytest.mark.asyncio
async def test_get_submission_id_from_link__old_post_link():
    post_id = 34433
    post = MockPost(post_id=post_id)
    api = MockAsyncYippiClient([post])
    handler = E621Handler(api)
    link = handler.find_links_in_str(post._post_link_old)[0]

    result = await handler.get_submission_id_from_link(link)

    assert result.submission_id == str(post_id)


@pytest.mark.asyncio
async def test_get_submission_id_from_link__safe_old_post_link():
    post_id = 34433
    post = MockPost(post_id=post_id)
    api = MockAsyncYippiClient([post])
    handler = E621Handler(api)
    link = handler.find_links_in_str(post._post_link_old_safe)[0]

    result = await handler.get_submission_id_from_link(link)

    assert result.submission_id == str(post_id)


@pytest.mark.asyncio
async def test_get_submission_id_from_link__direct_link():
    post_id = 34433
    post = MockPost(post_id=post_id)
    api = MockAsyncYippiClient([post])
    handler = E621Handler(api)
    link = handler.find_links_in_str(post._direct_link)[0]

    result = await handler.get_submission_id_from_link(link)

    assert result.submission_id == str(post_id)


@pytest.mark.asyncio
async def test_get_submission_id_from_link__thumb_link():
    post_id = 34433
    post = MockPost(post_id=post_id)
    api = MockAsyncYippiClient([post])
    handler = E621Handler(api)
    link = handler.find_links_in_str(post._direct_thumb_link)[0]

    result = await handler.get_submission_id_from_link(link)

    assert result.submission_id == str(post_id)


@pytest.mark.asyncio
async def test_get_submission_id_from_link__direct_link_safe():
    post_id = 34433
    post = MockPost(post_id=post_id)
    api = MockAsyncYippiClient([post])
    handler = E621Handler(api)
    link = handler.find_links_in_str(post._direct_link_safe)[0]

    result = await handler.get_submission_id_from_link(link)

    assert result.submission_id == str(post_id)


@pytest.mark.asyncio
async def test_get_submission_id_from_link__direct_link_no_results():
    post_id = 34433
    post = MockPost(post_id=post_id)
    api = MockAsyncYippiClient([])
    handler = E621Handler(api)
    link = handler.find_links_in_str(post._direct_link)[0]

    with pytest.raises(HandlerException):
        await handler.get_submission_id_from_link(link)


@pytest.mark.asyncio
async def test_get_submission_id_from_link__no_link():
    handler = E621Handler(MockAsyncYippiClient())
    link = SiteLink(handler.site_code, "hello world")

    result = await handler.get_submission_id_from_link(link)

    assert result is None


@pytest.mark.asyncio
async def test_send_submission(mock_client):
    post_id = 34433
    post = MockPost(post_id=post_id)
    api = MockAsyncYippiClient([post])
    handler = E621Handler(api)
    chat = MockChat(12345)
    reply_to = 64343
    prefix = "Some prefix"

    with mock.patch("fa_search_bot.sites.sendable.Sendable.send_message") as mock_send:
        await handler.send_submission(str(post_id), mock_client, chat, reply_to=reply_to, prefix=prefix, edit=True)

    mock_send.assert_called_once()
    assert mock_send.call_args.args == (mock_client, chat)
    assert mock_send.call_args.kwargs["reply_to"] == reply_to
    assert mock_send.call_args.kwargs["prefix"] == prefix
    assert mock_send.call_args.kwargs["edit"] is True


def test_is_valid_submission_id__int():
    test_str = "654322"
    api = MockAsyncYippiClient([])
    handler = E621Handler(api)

    assert handler.is_valid_submission_id(test_str)


def test_is_valid_submission_id__md5():
    test_str = "f00c4c885c530e82bba55dfc3b5734a4"
    api = MockAsyncYippiClient([])
    handler = E621Handler(api)

    assert handler.is_valid_submission_id(test_str)


def test_is_valid_submission_id__str():
    test_str = "hello world"
    api = MockAsyncYippiClient([])
    handler = E621Handler(api)

    assert not handler.is_valid_submission_id(test_str)


@pytest.mark.asyncio
async def test_submission_as_answer(mock_client):
    post_id = 34433
    post = MockPost(post_id=post_id)
    api = MockAsyncYippiClient([post])
    handler = E621Handler(api)
    mock_builder = Mock(InlineBuilder)
    exp_result = "tgrdsasdfds"
    sub_id = SubmissionID(handler.site_code, str(post_id))

    with mock.patch(
        "fa_search_bot.sites.sendable.Sendable.to_inline_query_result",
        return_value=async_return(exp_result),
    ) as mock_inline:
        result = await handler.submission_as_answer(sub_id, mock_builder)

    assert result == exp_result
    mock_inline.assert_called_once()
    assert mock_inline.call_args.args == (mock_builder,)


@pytest.mark.asyncio
async def test_submission_as_answer__md5(mock_client):
    post_id = 34433
    post_md5 = "f00c4c885c530e82bba55dfc3b5734a4"
    post = MockPost(post_id=post_id, md5=post_md5)
    api = MockAsyncYippiClient([post])
    handler = E621Handler(api)
    mock_builder = Mock(InlineBuilder)
    exp_result = "tgrdsasdfds"
    sub_id = SubmissionID(handler.site_code, post_md5)

    with mock.patch(
        "fa_search_bot.sites.sendable.Sendable.to_inline_query_result",
        return_value=async_return(exp_result),
    ) as mock_inline:
        result = await handler.submission_as_answer(sub_id, mock_builder)

    assert result == exp_result
    mock_inline.assert_called_once()
    assert mock_inline.call_args.args == (mock_builder,)
