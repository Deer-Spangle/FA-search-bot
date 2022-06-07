from unittest import mock

from fa_search_bot.subscription_watcher import SubscriptionWatcher
from fa_search_bot.tests.util.mock_export_api import MockExportAPI


def test_load_old_save_new(mock_client):
    old_data = {
        "latest_ids": ["38447607", "38447608", "38447609", "38447610"],
        "subscriptions": [
            {
                "query": "deer",
                "destination": -10053,
                "latest_update": "2020-09-20T11:11:19.329747",
            },
            {
                "query": "rating:safe rabbit",
                "destination": -76543,
                "latest_update": "2020-10-31T21:50:54.020924",
            },
            {
                "query": "@keywords deer",
                "destination": 34342,
                "latest_update": "2020-10-31T21:09:58.755093",
            },
            {
                "query": "@keywords dragon",
                "destination": 34342,
                "latest_update": "2020-10-31T21:09:58.755093",
            },
        ],
        "blacklists": {"87654": ["artist:fender", "fox"], "-76543": ["artist:fred"]},
    }
    api = MockExportAPI()

    def mock_load(*args, **kwargs):
        return old_data

    class MockDump:
        def __init__(self):
            self.dumped_data = None

        def call(self, data, *args, **kwargs):
            self.dumped_data = data

    mock_dump = MockDump()

    with mock.patch("json.loads", mock_load):
        watcher = SubscriptionWatcher.load_from_json(api, mock_client)

    assert len(watcher.subscriptions) == 4
    assert len(watcher.blocklists) == 2
    assert len(watcher.latest_ids) == 4

    with mock.patch("json.dump", mock_dump.call):
        watcher.save_to_json()

    new_data = mock_dump.dumped_data
    assert "latest_ids" in new_data
    assert new_data["latest_ids"] == old_data["latest_ids"]
    assert "destinations" in new_data
    assert len(new_data["destinations"]) == 4
    for destination in new_data["destinations"].values():
        assert "subscriptions" in destination
        assert "blocks" in destination
    # Check dest -10053
    dest1 = new_data["destinations"]["-10053"]
    assert len(dest1["subscriptions"]) == 1
    assert len(dest1["blocks"]) == 0
    assert dest1["subscriptions"][0] == {
        "query": "deer",
        "latest_update": "2020-09-20T11:11:19.329747",
        "paused": False,
    }
    # check dest -76543
    dest2 = new_data["destinations"]["-76543"]
    assert len(dest2["subscriptions"]) == 1
    assert len(dest2["blocks"]) == 1
    assert dest2["subscriptions"][0] == {
        "query": "rating:safe rabbit",
        "latest_update": "2020-10-31T21:50:54.020924",
        "paused": False,
    }
    assert dest2["blocks"][0] == {"query": "artist:fred"}
    # Check dest 34342
    dest3 = new_data["destinations"]["34342"]
    assert len(dest3["subscriptions"]) == 2
    assert len(dest3["blocks"]) == 0
    assert {
               "query": "@keywords deer",
               "latest_update": "2020-10-31T21:09:58.755093",
               "paused": False,
           } in dest3["subscriptions"]
    assert {
               "query": "@keywords dragon",
               "latest_update": "2020-10-31T21:09:58.755093",
               "paused": False,
           } in dest3["subscriptions"]
    # Check dest 87654
    dest4 = new_data["destinations"]["87654"]
    assert len(dest4["subscriptions"]) == 0
    assert len(dest4["blocks"]) == 2
    assert {"query": "artist:fender"} in dest4["blocks"]
    assert {"query": "fox"} in dest4["blocks"]
