import pytest

from fa_search_bot.sites.furaffinity.fa_handler import FAHandler


@pytest.mark.asyncio
async def test_submission_link_format(api):
    submission = await api.get_full_submission("19925704")
    handler = FAHandler(api)

    assert handler.FA_SUB_LINK.search(submission.link)


@pytest.mark.asyncio
async def test_direct_link_format(api):
    submission = await api.get_full_submission("19925704")
    handler = FAHandler(api)

    assert handler.FA_DIRECT_LINK.search(submission.download_url)


@pytest.mark.asyncio
async def test_thumb_link_format(api):
    submission = await api.get_full_submission("19925704")
    handler = FAHandler(api)

    assert handler.FA_THUMB_LINK.search(submission.thumbnail_url)
