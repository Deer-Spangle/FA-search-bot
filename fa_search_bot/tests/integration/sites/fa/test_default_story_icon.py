import pytest

from fa_search_bot.sites.fa_export_api import FAExportAPI


@pytest.mark.asyncio
async def test_default_icon_recognised():
    default_icon_sub = "572932"
    api = FAExportAPI("https://faexport.spangle.org.uk")
    sub = await api.get_full_submission(default_icon_sub)

    assert sub._has_default_story_pic()


@pytest.mark.asyncio
async def test_custom_icon_not_recognised():
    default_icon_sub = "42085964"
    api = FAExportAPI("https://faexport.spangle.org.uk")
    sub = await api.get_full_submission(default_icon_sub)

    assert not sub._has_default_story_pic()
