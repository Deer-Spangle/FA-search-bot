This is an experiment to check whether files are modified when being uploaded to telegram and downloaded again.

## Experiment (2023-03-11)
A large list of different file types were sent in one of 6 ways. Either they were sent via web URL, as raw bytes, or using a local file path. They were all sent with force_document true, or false.
For each send attempt, the result in telegram's linux desktop client was noted, and the file was downloaded and the md5 hash checked before and after.

## Conditions
These tests were conducted on 2023-03-11, sending files with telethon 1.12.1 on my laptop, and receiving them via the linux desktop client on the same laptop.

## Results
The results varied mainly by the method of sending, but in summary, sending as local file gave the most reliable and predictable results.
In most cases, sending as a document meant that the md5 was not changed. (Sending a gif as a web URL was the exception to this)
- Sending a file as a web URL:
  - Limited the resolution of images that could be sent, as expected from `telegram_image_size.md` experiment.
  - Photos and gifs did not preserve md5. Documents, stickers, videos all did.
  - Meant that small webp images sent as stickers, whether force_document was true or not
  - `force_document=True` did not behave as expected for mp4 files (with and without audio), gifs, and mp3 files
  - Sending gif as document did not preserve md5 hash. (It was converted into an mp4 without sound)
  - json files would send via url, but txt and webm files would not.
  - Disclaimer: exif metadata files tested were on local network, and therefore could not send via URL
- Sending a file as raw bytes:
  - jpg and png files arrived as photos (md5 was not preserved)
  - Everything else sent as a document without filename or thumbnail, preserving md5 hash of the original content.
  - `force_document=True` behaved exactly as expected, sending all file types as document (without filename or thumbnail)
- Sending a file as local file path:
  - Everything sent with `force_document=True` sent with filename and thumb, and md5 hash was preserved.
    - Even exif data, which had not been preserved when conducting this test sending from the android client. (Which implies the android client is stripping that exif data out, rather than telegram servers stripping it out)
  - Photos sent as photos did not preserve md5 hash, but all other file types preserved md5 hash in this format.
  - Silent mp4 files, and gif files, both sent as gifs when sent as photos. (gif files were not converted to mp4 files)
    - gif files, when sent as document, were still displayed as gifs (and were not converted to mp4 files)
  - webm and mkv video files, sent as document, displayed as videos in the linux desktop client
  - Small webp images sent as photos were displayed as stickers in the linux desktop client

## Results table
```text
+--------------------+-----+-------------+-----+-------------+-----+----------------+-----+----------------+-----+-------------+-----+-------------+
|                    | MD5 | sent format | MD5 | sent forma5 | MD5 | sent format    | MD5 | sent format    | MD5 | sent format | MD5 | sent forma5 |
|                    | by url            | by url            | by bytes             | by bytes             | by file path      | by file path      |
|          File type | as photo          | as doc            | as photo             | as doc               | as photo          | as doc            |
+--------------------+-----+-------------+-----+-------------+-----+----------------+-----+----------------+-----+-------------+-----+-------------+
|            png_100 |  N  | photo       |  Y  | doc         |  N  | photo          |  Y  | doc (no thumb) |  N  | photo       |  Y  | doc         |
|           png_1000 |  N  | photo       |  Y  | doc         |  N  | photo          |  Y  | doc (no thumb) |  N  | photo       |  Y  | doc         |
|           png_5000 |  -  | -           |  -  | -           |  N  | photo          |  Y  | doc (no thumb) |  N  | photo       |  Y  | doc         |
|           png_6000 |  -  | -           |  -  | -           |  N  | photo          |  Y  | doc (no thumb) |  N  | photo       |  Y  | doc         |
|            jpg_100 |  N  | photo       |  Y  | doc         |  N  | photo          |  Y  | doc (no thumb) |  N  | photo       |  Y  | doc         |
|           jpg_1000 |  N  | photo       |  Y  | doc         |  N  | photo          |  Y  | doc (no thumb) |  N  | photo       |  Y  | doc         |
|           jpg_5000 |  N  | photo       |  Y  | doc         |  N  | photo          |  Y  | doc (no thumb) |  N  | photo       |  Y  | doc         |
|           jpg_6000 |  -  | -           |  -  | -           |  N  | photo          |  Y  | doc (no thumb) |  N  | photo       |  Y  | doc         |
|         webp_small |  Y  | sticker     |  Y  | sticker     |  Y  | doc (no thumb) |  Y  | doc (no thumb) |  Y  | sticker     |  Y  | doc         |
|           wepb_big |  Y  | doc         |  Y  | doc         |  Y  | doc (no thumb) |  Y  | doc (no thumb) |  Y  | doc         |  Y  | doc         |
|               json |  Y  | doc         |  Y  | doc         |  Y  | doc (no thumb) |  Y  | doc (no thumb) |  Y  | doc         |  Y  | doc         |
|                txt |  -  | -           |  -  | -           |  Y  | doc (no thumb) |  Y  | doc (no thumb) |  Y  | doc         |  Y  | doc         |
|         mp4_silent |  Y  | gif         |  Y  | gif         |  Y  | doc (no thumb) |  Y  | doc (no thumb) |  Y  | gif         |  Y  | doc         |
|          mp4_audio |  Y  | video       |  Y  | video       |  Y  | doc (no thumb) |  Y  | doc (no thumb) |  Y  | video       |  Y  | doc         |
|                mkv |  Y  | doc         |  Y  | doc         |  Y  | doc (no thumb) |  Y  | doc (no thumb) |  Y  | video       |  Y  | doc         |
|                gif |  N  | gif         |  N  | gif         |  Y  | doc (no thumb) |  Y  | doc (no thumb) |  Y  | gif         |  Y  | gif         |
|               webm |  -  | -           |  -  | -           |  Y  | doc (no thumb) |  Y  | doc (no thumb) |  Y  | video       |  Y  | doc         |
|                mp3 |  Y  | audio       |  Y  | audio       |  Y  | doc (no thumb) |  Y  | doc (no thumb) |  Y  | audio       |  Y  | doc         |
|      jpg_with_exif |  -  | -           |  -  | -           |  N  | photo          |  Y  | doc (no thumb) |  N  | photo       |  Y  | doc         |
| mp4_with_metadata' |  -  | -           |  -  | -           |  Y  | doc (no thumb) |  Y  | doc (no thumb) |  Y  | video       |  Y  | doc         |
+--------------------+-----+-------------+-----+-------------+-----+----------------+-----+----------------+-----+-------------+-----+-------------+
```

## Conclusion
Sending via local file path gives the most predictable results, and md5 hash is preserved for all types except for when sending images as photos.

## The code
Swapping out BeepFunctionality for this
```python
TMP_DIR = "/tmp/fas_test_files/"
os.makedirs(TMP_DIR, exist_ok=True)


class BeepFunctionality(BotFunctionality):
    def __init__(self) -> None:
        super().__init__(events.NewMessage(pattern="/beep", incoming=True))

    file_urls_by_type = {
        "png_100": "https://images.unsplash.com/photo-1676558410062-d37d4793a3e5?crop=entropy&cs=tinysrgb&fit=crop&fm=png&h=100&ixlib=rb-4.0.3&q=80&w=100&ext=.png",
        "png_1000": "https://images.unsplash.com/photo-1677330888529-3b859572df7a?crop=entropy&cs=tinysrgb&fit=crop&fm=png&h=1000&ixlib=rb-4.0.3&q=80&w=1000&ext=.png",
        "png_5000": "https://images.unsplash.com/photo-1677583229810-c4577965f2c9?crop=entropy&cs=tinysrgb&fit=crop&fm=png&h=5000&ixlib=rb-4.0.3&q=80&w=5000&ext=.png",
        "png_6000": "https://images.unsplash.com/photo-1676393398356-38f325091013?crop=entropy&cs=tinysrgb&fit=crop&fm=png&h=6000&ixlib=rb-4.0.3&q=80&w=6000&ext=.png",
        "jpg_100": "https://images.unsplash.com/photo-1676558410062-d37d4793a3e5?crop=entropy&cs=tinysrgb&fit=crop&fm=jpg&h=100&ixlib=rb-4.0.3&q=80&w=100&ext=.jpg",
        "jpg_1000": "https://images.unsplash.com/photo-1677330888529-3b859572df7a?crop=entropy&cs=tinysrgb&fit=crop&fm=jpg&h=1000&ixlib=rb-4.0.3&q=80&w=1000&ext=.jpg",
        "jpg_5000": "https://images.unsplash.com/photo-1677583229810-c4577965f2c9?crop=entropy&cs=tinysrgb&fit=crop&fm=jpg&h=5000&ixlib=rb-4.0.3&q=80&w=5000&ext=.jpg",
        "jpg_6000": "https://images.unsplash.com/photo-1676393398356-38f325091013?crop=entropy&cs=tinysrgb&fit=crop&fm=jpg&h=6000&ixlib=rb-4.0.3&q=80&w=6000&ext=.jpg",
        "webp_small": "https://www.gstatic.com/webp/gallery/1.sm.webp",
        "wepb_big": "https://filesamples.com/samples/image/webp/sample1.webp",
        "json": "https://faexport.spangle.org.uk/submission/19925704.json",
        "txt": "https://filesamples.com/samples/document/txt/sample3.txt",
        "mp4_silent": "https://filesamples.com/samples/video/mp4/sample_960x540.mp4",
        "mp4_audio": "https://filesamples.com/samples/video/mp4/sample_960x400_ocean_with_audio.mp4",
        "mkv": "https://filesamples.com/samples/video/mkv/sample_960x540.mkv",
        "gif": "https://static1.e621.net/data/1c/71/1c7128428802a5f9e571a9e06c6cf80e.gif",
        "webm": "https://static1.e621.net/data/2a/73/2a7330d20e2230870649f1179e1d9d3c.webm",
        "mp3": "https://filesamples.com/samples/audio/mp3/sample1.mp3",
        "jpg_with_exif": "http://hoard/IMG_20230311_165255_1.jpg",
        "mp4_with_metadata": "http://hoard/VID_20230308_024915.mp4",
    }

    async def download_and_hash(self, msg: Message, ext: str) -> str:
        dl_path = TMP_DIR + f"dl_file.{ext}"
        os.makedirs(TMP_DIR, exist_ok=True)
        await msg.download_media(file=dl_path)
        with open(dl_path, "rb") as f:
            new_content = f.read()
        new_md5 = hashlib.md5(new_content).hexdigest()
        return f"{new_md5}"

    async def test_file_mode(self, event: events.NewMessage.Event, file: Union[str, bytes], message: str, ext: str, force_doc: bool) -> Optional[str]:
        try:
            resp = await event.reply(message, file=file, force_document=force_doc)
        except Exception:
            return None
        md5_hash = await self.download_and_hash(resp, ext)
        await resp.delete()
        return md5_hash

    async def test_file(self, event: events.NewMessage.Event, name: str, path: str) -> None:
        try_resp = await event.reply(f"Trying: {name}")
        ext = path.split(".")[-1]
        content = requests.get(path).content
        file_path = f"{TMP_DIR}/{name}.{ext}"
        with open(file_path, "wb") as f:
            f.write(content)
        my_md5 = hashlib.md5(content).hexdigest()
        md5_by_url_photo = await self.test_file_mode(event, path, f"sending {name} by url, as photo", ext, False)
        md5_by_url_doc = await self.test_file_mode(event, path, f"sending {name} by url, as document", ext, True)
        md5_by_bytes_photo = await self.test_file_mode(event, content, f"sending {name} by bytes, as photo", ext, False)
        md5_by_bytes_doc = await self.test_file_mode(event, content, f"sending {name} by bytes, as document", ext, True)
        md5_by_file_photo = await self.test_file_mode(event, file_path, f"sending {name} by file, as photo", ext, False)
        md5_by_file_doc = await self.test_file_mode(event, file_path, f"sending {name} by file, as document", ext, True)
        # Write report
        if md5_by_url_photo == my_md5:
            md5_by_url_photo = f"**{md5_by_url_photo}**"
        if md5_by_url_doc == my_md5:
            md5_by_url_doc = f"**{md5_by_url_doc}**"
        if md5_by_bytes_photo == my_md5:
            md5_by_bytes_photo = f"**{md5_by_bytes_photo}**"
        if md5_by_bytes_doc == my_md5:
            md5_by_bytes_doc = f"**{md5_by_bytes_doc}**"
        if md5_by_file_photo == my_md5:
            md5_by_file_photo = f"**{md5_by_file_photo}**"
        if md5_by_file_doc == my_md5:
            md5_by_file_doc = f"**{md5_by_file_doc}**"
        await event.reply(f"Report: `{name}`\nOriginal: {my_md5}\nPhoto by url: {md5_by_url_photo}\nDoc by url: {md5_by_url_doc}\nPhoto by bytes: {md5_by_bytes_photo}\nDoc by bytes: {md5_by_bytes_doc}\nPhoto by file: {md5_by_file_photo}\nDoc by file: {md5_by_file_doc}")
        await try_resp.delete()

    async def call(self, event: events.NewMessage.Event) -> None:
        logger.info("Beep")
        self.usage_counter.labels(function="beep").inc()
        for key, val in self.file_urls_by_type.items():
            if not val:
                continue
            try:
                await self.test_file(event, key, val)
            except Exception as e:
                await event.reply(f"Failed to test: {key}. {e}")
        await event.reply("Done")
        raise events.StopPropagation

    @property
    def usage_labels(self) -> List[str]:
        return ["beep"]
```