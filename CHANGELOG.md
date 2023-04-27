# Changelog

Changelog for FASearchBot, should include entries for these types of changes:

- `Added` for new features.
- `Changed` for changes in existing functionality.
- `Deprecated` for soon-to-be removed features.
- `Removed` for now removed features.
- `Fixed` for any bug fixes.
- `Security` in case of vulnerabilities. Format inspired by https://keepachangelog.com/en/1.0.0/

## [1.13.4] - 2023-04-27

### Added

- Added metrics on cache database size, `fasearchbot_db_cache_entries`
- Added metrics on saving and loading cache, cache hits and misses, to submission cache, `fasearchbot_submissioncache_*`
- Added metrics on inline query result counts, cached and fresh, `fasearchbot_inline_*_results_count`

## [1.13.3] - 2023-04-27

### Fixed

- Improved reliability of inline search, returning smaller batches of fresh results for speed, but sending larger 
  batches of cached results if available.

## [1.13.2] - 2023-04-24

### Added

- Added new metric, `fasearchbot_sentsubmission_sent_from_cache_total` storing how many messages are sent from cache.

### Fixed

- Subscription watcher to handle PeerIdInvalidError by pausing all subscriptions to that peer.

## [1.13.1] - 2023-04-24

### Fixed

- Subscription watcher will now send from cache correctly

## [1.13.0] - 2023-04-24

### Added

- Added a cache database that stores the file ID of all images sent in telegram, so that they can be sent much faster 
  the second time. This also came with a big refactor of the internals and site handling and such. Should make inline
  queries more reliable too! (By virtue of being faster)

## [1.12.6] - 2023-04-20

### Added

- Added a prometheus metric `fasearchbot_fasubwatcher_time_taken`, which is logging the time taken by the subscription 
  watcher performing various tasks. This merges the metric series which were added in version 1.12.5.

### Removed

- Removed the older metric series of the form `fasearchbot_fasubwatcher_time_taken_*`, to merge them all into one metric
  series with individual labels for different tasks

## [1.12.5] - 2023-04-18

### Added

- Added a series of prometheus metrics to the subscription watcher, logging the time taken by various stages of the
  subscription watcher's process. These are all of the form `fasearchbot_fasubwatcher_time_taken_*`

## [1.12.4] - 2023-04-04

### Added

- Added a prometheus metric `fasearchbot_fasubwatcher_latest_posted_at_unixtime`, which is the unix timestamp that the 
  latest processed submission was uploaded to FA

### Removed

- Removed the `fasearchbot_fasubwatcher_backlog_seconds` metric, which may become outdated or misleading

## [1.12.3] - 2023-04-04

### Added

- Added a prometheus metric `fasearchbot_fasubwatcher_backlog_seconds`, which says how many seconds old the latest 
  submission checked by the subscription watcher is. (i.e. how many seconds since it was posted on FA)

## [1.12.2] - 2022-11-24

### Added

- Added a prometheus metric `fasearchbot_fasubwatcher_subscription_destination_count_active`, which says how many
  destinations have at least one active subscription

## [1.12.1] - 2022-11-24

### Fixed

- Subscriptions will now be paused when the bot cannot access a channel

## [1.12.0] - 2021-12-02

### Added

- Ability to do inline e621 searches

### Changed

- Split apart inline functionality classes, for easier modification of gallery, search, and favourite inline queries

## [1.11.10] - 2021-11-27

### Security

- Updating direct indirect dependencies to fix security alerts. I don't believe any of these would pose serious security
  issues for this project.

## [1.11.9] - 2021-11-24

### Added

- Adding `g:` shortcode for inline user gallery searches
- Adding `f:` shortcode for inline user favourite searches

## [1.11.8] - 2021-11-23

### Added

- Add support for neatening e621 thumbnail links

## [1.11.7] - 2021-10-11

### Added

- Add support for e926 links

## [1.11.6] - 2021-09-25

### Changed

- Subscription terms which don't specify a field can now match the artist name

## [1.11.5] - 2021-08-19

### Added

- Add `fasearchbot_log_messages_total` metrics on log line counts by level

## [1.11.4] - 2021-08-19

### Added

- Added `fasearchbot_faapi_latest_id` metric, keeping note on the latest FA submission ID

### Changed

- Renamed `fasearchbot_fasubwatcher_updates_failed` metric to `fasearchbot_fasubwatcher_updates_failed_total`

### Fixed

- Fixing `fasearchbot_faapi_cloudflare_errors_total` metric, which had incorrect label naming

## [1.11.3] - 2021-08-18

### Added

- Lots of prometheus metrics on:
  - Running bot version and start up time
  - Functionality usage
  - API timings and error rates
  - Whether FA is in slow mode
  - Sent message counts and types
  - Gif and video conversion timings, error rates, and whether one or two pass conversion was required
  - Video types, lengths, and whether they have audio
  - Docker timings and error rates
  - Submissions processed by subscription handler, error rates and types, and rates of submissions which match
    subscriptions
  - Number of subscriptions and block lists, and destinations those are configured for
  - Backlog of submissions which need checking against subscriptions, and what time the last one was checked
- Added `prometheus_port` option to config to specify which port to run the metrics endpoint on, defaulting to 7065
- Supporting MD5 hashes as IDs for e621 submissions

### Removed

- Removed the usage logger at `logs-usage.log` (in favour of prometheus metrics)

## [1.11.2] - 2021-06-22

### Added

- Added e621 configuration to the config file. Set `e621` to a dictionary containing `username` and `password` keys.
  - This is so that the bot can access e621 posts which are not available to guests

### Changed

- Stop subscription watcher faster when told to stop (after the next submission, rather than after the next batch)
- Convert videos without audio which are over 40 seconds into videos, not gifs

### Fixed

- Handle images lacking an "is_animated" attribute, in case an image is named with the wrong file extension

## [1.11.1] - 2021-06-20

### Added

- Adding notes about e621 posts to welcome message

### Fixed

- Improve railroad diagram generation script
- Fixed two-pass video conversion such that it accommodates audio bitrate in its calculation of target video bitrate so
  that resulting videos are not above telegram size limits

## [1.11.0] - 2021-06-20

### Added

- Added support for e621
  - Reworking a lot of functionalities to handle e621 links
  - Creating Sendable to provide generic ways for functionalities to send submissions from different sites

### Fixed

- Fixed version number parsing to be a little less fragile

## [1.10.7] - 2021-06-12

### Changed

- In groups, neaten functionality should ignore gif and video captions, as well as image captions

## [1.10.6] - 2021-06-10

### Changed

- If a destination is removed, or the bot is blocked from it, pause all subscriptions to that destination

## [1.10.5] - 2021-06-10

### Changed

- Edit inline query messages after they are sent, to raise the quality level

## [1.10.4] - 2021-06-06

### Fixed

- Fixed loading of subscription data

## [1.10.3] - 2021-06-06

### Changed

- If subscription data file is empty, treat it as if it does not exist

## [1.10.2] - 2021-06-04

### Changed

- Adding title and author to non-image submissions (such as stories and music)
- Convert static gifs to png, so that telegram doesn't treat them as animated
- Separate github actions job for unit tests from telegram integration tests
- Creating website integration tests folder, for cases where we want to ensure a website behaves the same as we have
  assumed

## [1.10.1] - 2021-05-31

### Changed

- Handle gif conversions asynchronously, so it does not block all other actions

## [1.10.0] - 2021-05-30

### Added

- Added the ability to send individual submissions by passing the link or ID to an inline query

### Changed

- Creating generic SiteHandler base, and FAHandler implementation, laying the groundwork for supporting other websites

### Removed

- Removed no longer used python-telegram-bot dependency

## [1.9.2] - 2021-05-27

### Fixed

- Neaten now works in megagroups as well as groups

## [1.9.1] - 2021-05-25

### Fixed

- Fixed gallery display in inline photo query on mobile

## [1.9.0] - 2021-05-25

### Changed

- Switch from python-telegram-bot to Telethon
  - Allowing asynchronous operation
  - Better handling of flood limits
  - Better handling of errors when sending messages
- Switch subscription watcher from a separate thread, to an asynchronous task

## [1.8.10] - 2021-03-06

### Fixed

- No longer ignoring images with url buttons and no caption

## [1.8.9] - 2021-03-05

### Fixed

- Better handling and clarity around cloudflare errors

## [1.8.8] - 2021-03-03

### Fixed

- Fixed handling of messages without URL buttons

## [1.8.7] - 2021-03-03

### Changed

- Recommending @reverseSearchBot for looking up sources of gifs
- Checking URL buttons for links when messages are sent to the bot for neatening
- Replying to the unhandled message when warning that a message is unhandled

## [1.8.6] - 2021-02-23

### Changed

- No longer considering hypens and underscores to be word boundaries when checking subscription matches
- Only log usage of image hash recommend functionality in private message

## [1.8.5] - 2021-02-12

### Changed

- Switch from travis CI to github actions

### Fixed

- Switch to handling furaffinity.net direct and thumbnail links, as well as the old facdn.net links

## [1.8.4] - 2021-02-06

### Fixed

- Handling FA submissions without thumbnails

## [1.8.3] - 2021-02-06

### Changed

- Improved logging for deleted submissions in subscription watcher

## [1.8.2] - 2021-01-13

### Fixed

- Checking all submission IDs, rather than just the ones on browse listings, so that we don't miss scraps

## [1.8.1] - 2021-01-13

### Added

- Telegram integration tests running a full copy of the bot at a staging handle and sending messages to it
- Added notes on pause and resume functionality to readme

### Fixed

- Shutdown process closes all threads
- Fixed error where migrated chat would not recognise duplicate subscriptions

## [1.8.0] - 2020-11-04

### Added

- CodeQL static analysis

### Changed

- Subscriptions can now be configured in channels
- Requirements and tasks are now managed via poetry, rather than requirements.txt anbd makefile

## [1.7.6] - 2020-10-30

### Fixed

- Will no longer try and neaten links in channels, or links from image captions in groups

## [1.7.5] - 2020-09-28

### Added

- Experiment results on maximum telegram gif resolutions

### Changed

- Increased the maximum size of gifs to 1280x1280, (from 720x720)

## [1.7.4] - 2020-09-15

### Fixed

- Now supporting new d2.facdn and t2.facdn direct links

## [1.7.3] - 2020-09-10

### Added

- Experiment on maximum telegram image resolutions

### Fixed

- Made sending photos a bit more resilient, as random URLs seem to fail to embed in telegram bot API

## [1.7.2] - 2020-09-07

### Changed

- Checking registered users count on FA, and slowing down if site is in slowdown mode

## [1.7.1] - 2020-08-12

### Fixed

- Migrate chat subscriptions if a group is upgraded to supergroup

## [1.7.0] - 2020-08-07

### Added

- Added `except` keyword to subscription queries, such that wildcard queries can have exceptions they do not match

## [1.6.7] - 2020-08-05

### Changed

- Moved run.py out of the package and into the root directory

## [1.6.6] - 2020-08-05

### Added

- Added lots of logging and usage logging

### Changed

- Extracted MQBot class into a separate file

## [1.6.5] - 2020-07-29

### Fixed

- Message formatting errors for subscriptions with underscores, by switching from markdown to html message formatting

## [1.6.4] - 2020-07-29

### Changed

- Moved everything into fa_search_bot package

## [1.6.3] - 2020-07-29

### Changed

- Added link to FoxBot source code in readme

### Fixed

- Better handling of large images so that if they fail to send, a smaller version will be sent

## [1.6.2] - 2020-07-25

### Added

- Bot now sends prettier and better telegram-optimised gifs by using dockerised ffmpeg to convert them to mp4 files
- Funding link: ko-fi

## [1.6.1] - 2020-07-19

### Changed

- Making prefix and suffix subscription queries not match if the whole word is equal to the specified prefix/suffix

## [1.6.0] - 2020-07-19

### Added

- Complex subscription query parsing, with and/or, fields, phrases, ratings, prefix/suffix, and all sorts
- Added an experiment on doing this with whoosh, but ended up abandoning that and using pyparsing and custom matching

## [1.5.4] - 2020-07-14

### Changed

- If a submission matches multiple subscriptions in one chat, only one message is sent, with the list of matching
  subscriptions

## [1.5.3] - 2020-07-14

### Changed

- Added @FoxBot to the list of recommended bots to locate image sources, alongside @FindFurryPicBot

## [1.5.2] - 2020-07-14

### Added

- Added "!" as a negation modifier, alongside "-", for subscriptions

## [1.5.1] - 2020-07-13

### Fixed

- Allow subscriptions to be configured in channels

## [1.5.0] - 2020-07-13

### Added

- Subscriptions can now specify the rating of submissions

### Changed

- Renaming block list functionality
- Default to faexport.spangle.org.uk rather than faexport.boothale.net

## [1.4.3] - 2020-07-13

### Fixed

- Fix github repository link in welcome message

## [1.4.2] - 2020-05-09

### Added

- Added an error message when an unhandled message is sent to the bot

## [1.4.1] - 2020-05-08

### Added

- Added github link to the welcome message

## [1.4.0] - 2020-05-08

### Added

- Added in progress messages while the bot is searching for submission to neaten

### Changed

- Neatening up tests

## [1.3.7] - 2020-04-11

### Changed

- Subscription watcher should shutdown more quickly when asked to stop

### Fixed

- Fixing a bug that resulted in repeats when API was down, and instead keeps trying until API returns

## [1.3.6] - 2020-03-22

### Changed

- Updating python-telegram-bot
- Converting tests to pytest

## [1.3.5] - 2020-03-22

### Changed

- Subscription watcher will shutdown faster when asked to stop

### Fixed

- Network issues when getting new results will no longer kill subscription watcher

## [1.3.4] - 2020-03-21

### Fixed

- Writing subscription data to temp file, so that running out of disc space doesn't lead to data loss

## [1.3.3] - 2020-03-21

### Added

- Adding heartbeat pings to subscription watcher, so that downtime can be monitored

## [1.3.2] - 2020-02-09

### Changed

- Moving remaining filters around, merging changes from 1.2.9

## [1.3.1] - 2020-01-13

### Fixed

- Fixing the filter used for image hash recommendation

## [1.3.0] - 2020-01-13

### Added

- Recommending @FindFurryPicBot to find image sources, if they are sent without a link

## [1.2.9] - 2020-02-09

### Changed

- Pulling all functionality classes and filter classes out into their own files

## [1.2.8] - 2019-12-27

### Fixed

- Don't repost submissions on bot restart, save latest submission IDs after every post

## [1.2.7] - 2019-12-08

### Fixed

- Use message queue to avoid messages hitting flood limit and failing to send

## [1.2.6] - 2019-11-30

### Changed

- Load and send submissions one by one, rather than waiting to load them all before sending any to subscriptions

## [1.2.5] - 2019-11-29

### Fixed

- Fixing "list changed size during iteration" error in subscription watcher by copying subscription list before
  iterating it

## [1.2.4] - 2019-11-29

### Fixed

- Bot should now respond to commands with the username appended to them, such as commands sent in groups

## [1.2.3] - 2019-11-29

### Changed

- List subscriptions command should list them in order

## [1.2.2] - 2019-11-29

### Changed

- Speed up subscription watcher by fetching all submissions before checking subscriptions

## [1.2.1] - 2019-11-28

### Changed

- Adding prefix to subscription result posts, rather than having a separate message saying which subscription the
  submission was posted for

### Fixed

- Adding retry logic to the FA API handler, to handle intermittent errors

## [1.2.0] - 2019-11-10

### Added

- Initial version number
- Rest of the bot, technically.
