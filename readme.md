# FA search bot
This is a telegram bot which can:
- Neaten up FA links into photos/documents, with captions
- Neaten up FA links by direct file link

Future feature plans:
- Inline FA searches
- FA subscriptions
- FA notifications

## Setup
To set this up, you'll need to:
 - Download or clone the repo
 - Install requirements: `pip install -r requirements.txt`
 - Add a `config.json` in the base directory, like so:
```json
{
  "bot_key": "---",
  "api_url": "https://faexport.boothale.net/"
}
```
with `bot_key` set to your telegram bot API key, and `api_url` set to the URL of a valid deployment of [the FA API](https://github.com/boothale/faexport).
 - Run `python3 run.py`
