from fa_search_bot.sites.fa_handler import FAHandler


def test_submission_link_format(api):
    submission = await api.get_full_submission("19925704")
    handler = FAHandler(api)

    assert handler.FA_SUB_LINK.match(submission.link)


def test_direct_link_format(api):
    submission = await api.get_full_submission("19925704")
    handler = FAHandler(api)

    assert handler.FA_DIRECT_LINK.match(submission.download_url)


def test_thumb_link_format(api):
    submission = await api.get_full_submission("19925704")
    handler = FAHandler(api)

    assert handler.FA_THUMB_LINK.match(submission.thumbnail_url)
