This is an experiment in which file information is required to store a sent file, and resend it.

## Results (2023-03-06)
You just need to store the file.media.id, the file.media.access_hash, and whether it was a photo or a document.

Swapping out the call() method in BeepFunctionality, for this:
```python
    async def call(self, event: events.NewMessage.Event) -> None:
        logger.info("Beep")
        self.usage_counter.labels(function="beep").inc()
        url = "https://dummyimage.com/100x100.png"
        my_file = requests.get(url).content
        my_md5 = hashlib.md5(my_file).hexdigest()
        resp = await event.reply("File from URL", file=url)
        is_photo: bool = isinstance(resp.file.media, telethon.tl.types.Photo)
        media_id: int = resp.file.media.id
        access_hash: int = resp.file.media.access_hash
        input_media = (InputPhoto if is_photo else InputDocument)(media_id, access_hash, b"")
        await event.reply("Sending as input media", file=input_media)
        await event.reply(f"boop. Mine was {my_md5}")
        raise events.StopPropagation
```