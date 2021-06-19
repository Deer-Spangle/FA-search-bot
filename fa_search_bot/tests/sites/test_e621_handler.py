from unittest import mock
from unittest.mock import Mock

import pytest
from telethon.tl.custom import InlineBuilder

from fa_search_bot.sites.e621_handler import E621Handler
from fa_search_bot.sites.site_handler import HandlerException
from fa_search_bot.tests.conftest import MockChat
from fa_search_bot.tests.util.mock_e621_client import MockPost, MockAsyncYippiClient


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
    assert any(result in post._post_link for result in results)
    assert any(result in post._post_link_old for result in results)
    assert any(result in post._direct_link for result in results)


@pytest.mark.asyncio
async def test_get_submission_id_from_link__post_link():
    post_id = 34433
    post = MockPost(post_id=post_id)
    api = MockAsyncYippiClient([post])
    handler = E621Handler(api)
    link = handler.find_links_in_str(post._post_link)[0]

    result = await handler.get_submission_id_from_link(link)

    assert result == post_id


@pytest.mark.asyncio
async def test_get_submission_id_from_link__old_post_link():
    post_id = 34433
    post = MockPost(post_id=post_id)
    api = MockAsyncYippiClient([post])
    handler = E621Handler(api)
    link = handler.find_links_in_str(post._post_link_old)[0]

    result = await handler.get_submission_id_from_link(link)

    assert result == post_id


@pytest.mark.asyncio
async def test_get_submission_id_from_link__direct_link():
    post_id = 34433
    post = MockPost(post_id=post_id)
    api = MockAsyncYippiClient([post])
    handler = E621Handler(api)
    link = handler.find_links_in_str(post._direct_link)[0]

    result = await handler.get_submission_id_from_link(link)

    assert result == post_id


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

    result = await handler.get_submission_id_from_link("hello world")

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
        await handler.send_submission(
            post_id,
            mock_client,
            chat,
            reply_to=reply_to,
            prefix=prefix,
            edit=True
        )

    mock_send.assert_called_once()
    assert mock_send.call_args.args == (mock_client, chat)
    assert mock_send.call_args.kwargs['reply_to'] == reply_to
    assert mock_send.call_args.kwargs['prefix'] == prefix
    assert mock_send.call_args.kwargs['edit'] is True


@pytest.mark.asyncio
async def test_submission_as_answer(mock_client):
    post_id = 34433
    post = MockPost(post_id=post_id)
    api = MockAsyncYippiClient([post])
    handler = E621Handler(api)
    mock_builder = Mock(InlineBuilder)
    exp_result = "tgrdsasdfds"

    with mock.patch(
            "fa_search_bot.sites.sendable.Sendable.to_inline_query_result", return_value=exp_result
    ) as mock_inline:
        result = await handler.submission_as_answer(
            post_id,
            mock_builder
        )

    assert result == exp_result
    mock_inline.assert_called_once()
    assert mock_inline.call_args.args == (mock_builder,)
