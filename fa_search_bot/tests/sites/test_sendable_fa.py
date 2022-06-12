from fa_search_bot.sites.fa_handler import SendableFASubmission
from fa_search_bot.sites.sendable import CaptionSettings
from fa_search_bot.tests.util.submission_builder import SubmissionBuilder


def test_caption():
    submission = SubmissionBuilder().build_full_submission()
    sendable = SendableFASubmission(submission)
    settings = CaptionSettings()

    caption = sendable.caption(settings)

    assert caption == sendable.link


def test_caption_prefix():
    submission = SubmissionBuilder().build_full_submission()
    sendable = SendableFASubmission(submission)
    settings = CaptionSettings()
    prefix = "example prefix"

    caption = sendable.caption(settings, prefix)

    assert caption.startswith(prefix)
    assert caption.endswith(sendable.link)


def test_caption_direct_link():
    submission = SubmissionBuilder().build_full_submission()
    sendable = SendableFASubmission(submission)
    settings = CaptionSettings(direct_link=True)

    caption = sendable.caption(settings)

    assert sendable.link in caption
    assert sendable.download_url in caption


def test_caption_author():
    submission = SubmissionBuilder().build_full_submission()
    sendable = SendableFASubmission(submission)
    settings = CaptionSettings(author=True)

    caption = sendable.caption(settings)

    assert sendable.link in caption
    assert submission.author.name in caption
    assert submission.author.link in caption


def test_caption_title():
    submission = SubmissionBuilder().build_full_submission()
    sendable = SendableFASubmission(submission)
    settings = CaptionSettings(title=True)

    caption = sendable.caption(settings)

    assert sendable.link in caption
    assert f'"{submission.title}"' in caption
