import pytest

from fa_search_bot.sites.e621.e621_handler import E621Post


@pytest.mark.asyncio
async def test_post_swf__preview(yippi_client):
    post = await yippi_client.post(239769)
    e621_post = E621Post(post)

    preview_link = e621_post.preview_image_url

    assert preview_link.split(".")[-1] in ["png", "jpg"]


@pytest.mark.asyncio
async def test_post_swf__thumbnail(yippi_client):
    post = await yippi_client.post(239769)
    e621_post = E621Post(post)

    thumb_link = e621_post.thumbnail_url

    assert thumb_link.split(".")[-1] in ["png", "jpg"]


@pytest.mark.asyncio
async def test_post_webm__preview(yippi_client):
    post = await yippi_client.post(1017424)
    e621_post = E621Post(post)

    preview_link = e621_post.preview_image_url

    assert preview_link.split(".")[-1] in ["png", "jpg"]


@pytest.mark.asyncio
async def test_post_webm__thumbnail(yippi_client):
    post = await yippi_client.post(1017424)
    e621_post = E621Post(post)

    thumb_link = e621_post.thumbnail_url

    assert thumb_link.split(".")[-1] in ["png", "jpg"]
