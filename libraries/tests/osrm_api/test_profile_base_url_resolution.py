import requests

from libraries.classes.osrm_api import OSRMClient


class _DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_route_uses_newyork_base_url_with_car_path(monkeypatch):
    calls = []

    def fake_get(url, params=None):
        calls.append((url, params))
        return _DummyResponse(
            {
                "routes": [
                    {
                        "legs": [
                            {
                                "steps": [
                                    {
                                        "distance": 1.0,
                                        "duration": 1.0,
                                        "geometry": "??",
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        )

    monkeypatch.setattr(requests, "get", fake_get)

    client = OSRMClient(base_url="local", profile="foot")
    client.route(
        [
            {"lon": -73.96, "lat": 40.65},
            {"lon": -73.95, "lat": 40.66},
        ],
        profile="car-newyork",
        steps=True,
    )

    assert len(calls) == 1
    url, params = calls[0]
    assert url.startswith("http://localhost:5003/route/v1/car/")
    assert params["steps"] == "true"


def test_route_hamilton_path_preserves_newyork_profile(monkeypatch):
    calls = []

    def fake_get(url, params=None):
        calls.append((url, params))
        return _DummyResponse(
            {
                "routes": [
                    {
                        "legs": [
                            {
                                "steps": [
                                    {
                                        "distance": 1.0,
                                        "duration": 1.0,
                                        "geometry": "??",
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        )

    monkeypatch.setattr(requests, "get", fake_get)

    client = OSRMClient(base_url="local", profile="foot")
    steps = client.route_hamilton_path(
        [
            {"lon": -73.96, "lat": 40.65},
            {"lon": -73.95, "lat": 40.66},
            {"lon": -73.94, "lat": 40.67},
        ],
        profile="car-newyork",
        problem_type="HPP",
    )

    assert len(steps) == 2
    assert len(calls) == 2
    assert all(url.startswith("http://localhost:5003/route/v1/car/") for url, _ in calls)
