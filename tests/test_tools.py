import pytest

from ollamarama.tools.math import calculate_expression
from ollamarama.tools.text import text_stats
from ollamarama.tools.utils import get_time
from ollamarama.tools import web, weather


# -- math: arithmetic + safety -------------------------------------------------

def test_calculate_basic_arithmetic():
    assert calculate_expression("2 + 3 * 4")["result"] == 14.0
    assert calculate_expression("-2 ** 2")["result"] == -4.0
    assert calculate_expression("7 % 3")["result"] == 1.0


@pytest.mark.parametrize(
    "expr",
    [
        "__import__('os').system('echo hi')",
        "os.getcwd()",
        "open('/etc/passwd').read()",
        "1 if True else 2",
        "[].append(1)",
        "lambda: 1",
        "a + 1",
    ],
)
def test_calculate_rejects_non_arithmetic(expr):
    # The AST evaluator must refuse anything that isn't pure arithmetic.
    assert calculate_expression(expr) == {"error": "Invalid arithmetic expression."}


def test_calculate_division_by_zero_is_handled():
    assert "error" in calculate_expression("1/0")


# -- text ----------------------------------------------------------------------

def test_text_stats_counts():
    out = text_stats("Hello world. How are you?")
    assert out["words"] == 5
    assert out["sentences"] == 2
    assert out["characters"] == len("Hello world. How are you?")


def test_text_stats_empty():
    assert text_stats("   ") == {"words": 0, "characters": 0, "sentences": 0}


# -- utils (time) --------------------------------------------------------------

def test_get_time_utc():
    out = get_time("UTC")
    assert out["timezone"] == "UTC"
    assert "T" in out["datetime"]


def test_get_time_invalid_timezone():
    assert "error" in get_time("Not/AZone")


# -- web (mocked network) ------------------------------------------------------

def test_fetch_url_truncates(monkeypatch):
    class Resp:
        status_code = 200
        text = "x" * 100

        def raise_for_status(self):
            pass

    monkeypatch.setattr(web.requests, "get", lambda *a, **k: Resp())
    out = web.fetch_url("http://example.com", max_bytes=10)
    assert out["truncated"] is True
    assert len(out["content"]) == 10
    assert out["status"] == 200


def test_fetch_url_request_error(monkeypatch):
    def boom(*a, **k):
        raise web.requests.RequestException("nope")

    monkeypatch.setattr(web.requests, "get", boom)
    assert "error" in web.fetch_url("http://example.com")


# -- weather (mocked network) --------------------------------------------------

def test_get_weather_invalid_city():
    assert "error" in weather.get_weather("")


def test_get_weather_city_not_found(monkeypatch):
    class Geo:
        def raise_for_status(self):
            pass

        def json(self):
            return {"results": []}

    monkeypatch.setattr(weather.requests, "get", lambda *a, **k: Geo())
    assert weather.get_weather("Nowhere")["error"].startswith("City not found")


def test_get_weather_success(monkeypatch):
    calls = []

    class Geo:
        def raise_for_status(self):
            pass

        def json(self):
            return {"results": [{"name": "Paris", "country": "France",
                                 "latitude": 48.85, "longitude": 2.35}]}

    class Wx:
        def raise_for_status(self):
            pass

        def json(self):
            return {"current_weather": {"temperature": 18.0, "windspeed": 5.0, "weathercode": 1}}

    def fake_get(url, *a, **k):
        calls.append(url)
        return Geo() if "geocoding" in url else Wx()

    monkeypatch.setattr(weather.requests, "get", fake_get)
    out = weather.get_weather("Paris", units="imperial")
    assert out["location"] == "Paris, France"
    assert out["temperature"] == 18.0
    assert out["temperature_unit"] == "°F"
    assert out["description"] == "mainly clear"
