# FA search bot
This is a telegram bot which can:
- Neaten up FA links into photos/documents, with captions.
- Neaten up FA links by direct file link.
- Inline FA searches. Also gallery, scraps and favourites browsing.
- Subscribe to queries on FA, and receive notifications when new matching results are posted.

Future feature plans:
- FA notifications

You can use it freely at [@FASearchBot](https://t.me/FASearchBot), add it to your own chats and channels, or use it inline anywhere by mentioning it

## Commands

### Neaten

Private message it a link to a Fur Affinity submission page, thumbnail url or image download url, i.e, a link beginning with `http://?.facdn.net/art/` and it will reply with the image's thumbnail and a link to that image's gallery page.

### Inline Responses

In any chat, mention the bot and pass it a Fur Affinity search query
`@FASearchBot [query]` and pick from the inline results which image you'd like to share.

You can also use these qualifiers inline:
`@FASearchBot gallery:username`
`@FASearchBot scraps:username`
`@FASearchBot favs:username`

#### Inline Search Queries

The bot will support all Fur Affinity queries, and some extra filter options:

Taken from FurAffinity's search documentation: 
> Search understands basic boolean operators:
> * AND: `hello & world`
> * OR : `hello | world`
> * NOT: `hello -world` -or- `hello !world`
> 
> Grouping: `(hello world)`
> Example: `( cat -dog ) | ( cat -mouse)`
>
> *Capabilities*
> Field searching: `@title hello @message world`
> Phrase searching: `"hello world"`
> Word proximity searching: `"hello world"~10`
> Quorum matching: `"the world is a wonderful place"/3`
> Example: `"hello world" @title "example program"~5 @message python -(php|perl)`
> 
> Available Fields: `@title` `@message` `@filename` `@lower` (artist name as it appears in their userpage URL) `@keywords`
> Example: `fender @title fender -dragoneer -ferrox @message -rednef -dragoneer`

### Subscriptions

`/add_subscription [query]`
`/list_subscriptions`
`/remove subscription [query]`

`/add_blocklisted_tag [tag]`
`/list_blocklisted_tags`
`/remove_blocklisted_tag [tag]`

#### Subscription queries

Subscriptions understand basic boolean operators:
- `-`, `!`, or `not` to exclude from the results, e.g. `taur -ych -rating:adult`
- `and` and `or` to combine options, e.g. `taur or centaur`
- You can use brackets too, e.g. `(taur or centaur) and not ych`

Phrases can be specified with quotation marks, e.g. `"open ych" -reminder`

And fields can be specified:
- `keywords:deer` (or `tags:deer`, `@keyword deer`)
- `title:free` (or `@title free`)
- `description:dragoness` (or `message: dragoness`)
- `artist:rajii` (or `author:rajii`, `uploader:rajii`, `poster:rajii`, `@lower rajii`, etc)
- `rating:general` (or `rating:safe`)
- `rating:mature` (or `rating:questionable`)
- `rating:adult` (or `rating:explicit`)

You can also combine fields with other operators, for example using one of the negation operators
 to exclude from the results, e.g. `taur -ych -rating:adult`

Words can also be given with asterisks to allow prefixes or suffixes, e.g. `multi*`, `*taur`

### Miscellaneous

`/beep` - responds with `boop`

Send or forward the bot an image with no text as a private message, and it will recommend you try [@foxbot](https://t.me/foxbot) or [@FindFurryPicBot](https://t.me/FindFurryPicBot) 

## Development 

### Running the bot for yourself

To set this up, you'll need to:

 - Download or clone the repo
 - Install requirements: `pip install -r requirements.txt`
 - Add a `config.json` in the base directory, like so:

```json
{
  "bot_key": "---",
  "api_url": "https://faexport.spangle.org.uk"
}
```

with `bot_key` set to your telegram bot API key, and `api_url` set to the URL of a valid deployment of [the FA API](https://github.com/Deer-Spangle/faexport).
 - Run `python3 run.py`
