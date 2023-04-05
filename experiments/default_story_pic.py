####
# This was an attempt to detect default story icons for:
# https://github.com/Deer-Spangle/FA-search-bot/issues/14
# But it turned out I don't need to do that at all.
####
import hashlib
import io
import string
from typing import Optional

import pytest
import requests
from PIL import ImageDraw, Image

from fa_search_bot.sites.furaffinity.fa_export_api import FAExportAPI
from fa_search_bot.sites.furaffinity.fa_submission import FASubmissionFull


class FASubmissionFullWithDefaultStoryIconDetection(FASubmissionFull):
    DEFAULT_STORY_ICON_SIZE = 2032
    DEFAULT_STORY_ICON_MD5 = "a4a6d1c090e7f06b7b97bb2a01865cfa"

    @classmethod
    def from_sub_full(cls, full_sub: FASubmissionFull):
        return cls(
            full_sub.submission_id,
            full_sub.thumbnail_url,
            full_sub.download_url,
            full_sub.full_image_url,
            full_sub.title,
            full_sub.author,
            full_sub.description,
            full_sub.keywords,
            full_sub.rating
        )

    def _has_default_story_pic_size(self) -> bool:
        if self.full_image_url is None:
            return False
        head = requests.head(self.full_image_url)
        try:
            file_size = int(head.headers['content-length'])
        except ValueError:
            return False
        return file_size == self.DEFAULT_STORY_ICON_SIZE

    def _has_default_story_pic(self) -> bool:
        if not self._has_default_story_pic_size():
            return False
        data = requests.get(self.full_image_url).content
        m = hashlib.md5()
        m.update(data)
        return m.hexdigest().lower() == self.DEFAULT_STORY_ICON_MD5.lower()

    def _generate_story_icon(self) -> Optional[bytes]:
        if not self._has_default_story_pic_size():
            return None
        data = requests.get(self.full_image_url).content
        img = Image.open(io.BytesIO(data))
        img = img.convert("RGB")
        img = img.resize((200, 200), Image.ANTIALIAS)
        draw = ImageDraw.Draw(img)
        acceptable_chars = set(string.digits + string.ascii_letters + string.punctuation + " ")
        clean_title = "".join(filter(lambda x: x in set(acceptable_chars), self.title))
        draw.text((20, 30), clean_title)
        draw.text((20, 150), f"By: {self.author.name}")
        byte_arr = io.BytesIO()
        img.save(byte_arr, format="PNG")
        return byte_arr.getvalue()


@pytest.mark.asyncio
async def test_default_icon_recognised():
    default_icon_sub = "572932"
    api = FAExportAPI("https://faexport.spangle.org.uk")
    full = await api.get_full_submission(default_icon_sub)
    sub = FASubmissionFullWithDefaultStoryIconDetection.from_sub_full(full)

    assert sub._has_default_story_pic()


@pytest.mark.asyncio
async def test_custom_icon_not_recognised():
    default_icon_sub = "42085964"
    api = FAExportAPI("https://faexport.spangle.org.uk")
    full = await api.get_full_submission(default_icon_sub)
    sub = FASubmissionFullWithDefaultStoryIconDetection.from_sub_full(full)

    assert not sub._has_default_story_pic()
