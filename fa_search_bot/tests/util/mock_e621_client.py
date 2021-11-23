import random
import uuid
from typing import List, Union, Optional

from yippi import Post, AsyncYippiClient


class MockPost(Post):

    def __init__(self, *, post_id: int = None, md5: str = None, ext: str = "jpg"):
        file_w, file_h = random.randint(100, 10_000), random.randint(100, 10_000)
        file_size = random.randint(200_000, 10_000_000)
        self._ext = ext
        self.md5 = md5 or uuid.uuid4().hex
        super().__init__({
            "id": post_id or random.randint(100_000, 999_999),
            "file": {
                "width": file_w,
                "height": file_h,
                "ext": ext,
                "size": file_size,
                "md5": md5,
                "url": self._direct_link
            }
        })

    @property
    def _post_link(self):
        return f"https://e621.net/posts/{self.id}/"

    @property
    def _post_link_safe(self):
        return f"https:/e926.net/posts/{self.id}/"

    @property
    def _post_link_old(self):
        return f"https://e621.net/post/show/{self.id}/"

    @property
    def _post_link_old_safe(self):
        return f"https://e926.net/post/show/{self.id}/"

    @property
    def _direct_link(self):
        return f"https://static.e621.net/data/{self.md5[:2]}/{self.md5[2:4]}/{self.md5}.{self._ext}"

    @property
    def _direct_thumb_link(self):
        return f"https://static.e621.net/data/sample/{self.md5[:2]}/{self.md5[2:4]}/{self.md5}.{self._ext}"

    @property
    def _direct_link_safe(self):
        return f"https://static.e926.net/data/{self.md5[:2]}/{self.md5[2:4]}/{self.md5}.{self._ext}"


class MockAsyncYippiClient(AsyncYippiClient):

    def __init__(self, mock_posts: List[MockPost] = None, *args, **kwargs):
        self._posts = mock_posts or []
        super().__init__("MockYippiClient", 0.1, "dr-spangle", *args, **kwargs)

    async def post(
            self,
            post_id: int
    ) -> Optional[Post]:
        return next(filter(lambda post: post.id == post_id, self._posts), None)

    async def posts(
            self,
            tags: Union[List, str] = None,
            limit: int = None,
            page: Union[int, str] = None,
    ) -> List[Post]:
        if not tags:
            return self._posts
        tags_split = tags
        if isinstance(tags, str):
            tags_split = tags.split()
        filters = []
        for tag in tags_split:
            if tag.startswith("md5:"):
                md5 = tag.split(":")[1]
                filters.append(lambda post: post.md5 == md5)
                continue
            raise NotImplementedError
        return list(filter(lambda post: all(f(post) for f in filters), self._posts))
