import datetime
import unittest

from subscription_watcher import Subscription


class SubscriptionTest(unittest.TestCase):

    def test_init(self):
        query = "yo"
        destination = 12432

        sub = Subscription(query, destination)

        assert sub.query == query
        assert sub.destination == destination
        assert sub.latest_update is None

    def test_matches_result(self):
        assert False
        pass  # TODO

    def test_to_json_no_updates(self):
        sub = Subscription("test query", -12322)

        data = sub.to_json()
        assert "query" in data
        assert data["query"] == "test query"
        assert "destination" in data
        assert data["destination"] == -12322
        assert "latest_update" in data
        assert data["latest_update"] is None

    def test_to_json(self):
        sub = Subscription("test query", -12322)
        sub.latest_update = datetime.datetime(2019, 9, 17, 21, 8, 35)

        data = sub.to_json()
        assert "query" in data
        assert data["query"] == "test query"
        assert "destination" in data
        assert data["destination"] == -12322
        assert "latest_update" in data
        assert data["latest_update"] == "2019-09-17T21:08:35"

    def test_from_json_no_update(self):
        data = {
            "query": "example query",
            "destination": 17839,
            "latest_update": None
        }

        sub = Subscription.from_json(data)
        assert sub.query == "example query"
        assert sub.destination == 17839
        assert sub.latest_update is None

    def test_from_json(self):
        data = {
            "query": "example query",
            "destination": 17839,
            "latest_update": "2019-09-17T21:14:07Z"
        }

        sub = Subscription.from_json(data)
        assert sub.query == "example query"
        assert sub.destination == 17839
        assert sub.latest_update == datetime.datetime(2019, 9, 17, 21, 14, 7, tzinfo=datetime.timezone.utc)

    def test_to_json_and_back_no_update(self):
        sub = Subscription("an example", -63939)

        data = sub.to_json()
        new_sub = Subscription.from_json(data)

        assert new_sub.query == sub.query
        assert new_sub.destination == sub.destination
        assert new_sub.latest_update == sub.latest_update

    def test_to_json_and_back(self):
        sub = Subscription("something", 3223)
        sub.latest_update = datetime.datetime(2019, 9, 17, 21, 16, 14, tzinfo=datetime.timezone.utc)

        data = sub.to_json()
        new_sub = Subscription.from_json(data)

        assert new_sub.query == sub.query
        assert new_sub.destination == sub.destination
        assert new_sub.latest_update == sub.latest_update
