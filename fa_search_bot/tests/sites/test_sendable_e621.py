from unittest.mock import Mock

from yippi import Post

from fa_search_bot.sites.e621.e621_handler import E621Post
from fa_search_bot.sites.sendable import CaptionSettings


def test_caption():
    mock_post = Mock(Post)
    mock_post.id = 12765
    sendable = E621Post(mock_post)
    settings = CaptionSettings()

    caption = sendable.caption(settings)

    assert caption == sendable.link


def test_caption_prefix():
    mock_post = Mock(Post)
    mock_post.id = 874545
    sendable = E621Post(mock_post)
    settings = CaptionSettings()
    prefix = "This is a prefix"

    caption = sendable.caption(settings, prefix)

    assert caption.startswith(prefix)
    assert caption.endswith(sendable.link)


def test_caption_direct_link():
    mock_post = Mock(Post)
    mock_post.id = 23823
    mock_post.file = {"url": "e621 example link"}
    sendable = E621Post(mock_post)
    settings = CaptionSettings(direct_link=True)

    caption = sendable.caption(settings)

    assert caption.startswith(sendable.link)
    assert sendable.download_url in caption


def test_preview_image():
    mock_post = Mock(Post)
    mock_post.file = {"url": "download url.jpg", "ext": "jpg"}
    mock_post.preview = {"url": "preview url"}
    mock_post.sample = {"url": "sample url"}
    sendable = E621Post(mock_post)

    preview_url = sendable.preview_image_url

    assert preview_url == "download url.jpg"


def test_preview_image__swf():
    mock_post = Mock(Post)
    mock_post.file = {"url": "download url.swf", "ext": "swf"}
    mock_post.preview = {"url": "preview url"}
    mock_post.sample = {"url": "sample url"}
    sendable = E621Post(mock_post)

    preview_url = sendable.preview_image_url

    assert preview_url == "preview url"


def test_preview_image__webm():
    mock_post = Mock(Post)
    mock_post.file = {"url": "download url.webm", "ext": "webm"}
    mock_post.preview = {"url": "preview url"}
    mock_post.sample = {"url": "sample url"}
    sendable = E621Post(mock_post)

    preview_url = sendable.preview_image_url

    assert preview_url == "sample url"


def test_thumbnail_image():
    mock_post = Mock(Post)
    mock_post.file = {"url": "download url.jpg", "ext": "jpg"}
    mock_post.preview = {"url": "preview url"}
    mock_post.sample = {"url": "sample url"}
    sendable = E621Post(mock_post)

    preview_url = sendable.thumbnail_url

    assert preview_url == "sample url"


def test_thumbnail_image__swf():
    mock_post = Mock(Post)
    mock_post.file = {"url": "download url.swf", "ext": "swf"}
    mock_post.preview = {"url": "preview url"}
    mock_post.sample = {"url": "sample url"}
    sendable = E621Post(mock_post)

    preview_url = sendable.thumbnail_url

    assert preview_url == "preview url"
