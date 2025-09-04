from __future__ import annotations

from typing import Dict, Any

import requests


def _units_map(units: str) -> Dict[str, str]:
    u = (units or "metric").lower()
    if u in ("imperial", "us"):
        return {"temperature_unit": "fahrenheit", "windspeed_unit": "mph"}
    return {"temperature_unit": "celsius", "windspeed_unit": "kmh"}


def _code_desc(code: int) -> str:
    mapping = {
        0: "clear sky",
        1: "mainly clear",
        2: "partly cloudy",
        3: "overcast",
        45: "fog",
        48: "depositing rime fog",
        51: "light drizzle",
        53: "moderate drizzle",
        55: "dense drizzle",
        61: "slight rain",
        63: "moderate rain",
        65: "heavy rain",
        71: "slight snow",
        73: "moderate snow",
        75: "heavy snow",
        80: "rain showers",
        81: "heavy rain showers",
        82: "violent rain showers",
        95: "thunderstorm",
        96: "thunderstorm with hail",
        99: "severe thunderstorm with hail",
    }
    return mapping.get(code, f"code {code}")


def get_weather(city: str, units: str = "metric") -> Dict[str, Any]:
    if not city or not isinstance(city, str):
        return {"error": "Invalid 'city' argument; expected a non-empty string."}

    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
            timeout=20,
        )
        geo.raise_for_status()
        data = geo.json() or {}
        results = data.get("results") or []
        if not results:
            return {"error": f"City not found: {city}"}
        r0 = results[0]
        name = r0.get("name") or city
        country = r0.get("country") or ""
        lat = r0.get("latitude")
        lon = r0.get("longitude")
        if lat is None or lon is None:
            return {"error": f"Failed to geocode: {city}"}

        unit_params = _units_map(units)
        wx = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
                **unit_params,
            },
            timeout=20,
        )
        wx.raise_for_status()
        wdata = wx.json() or {}
        cw = (wdata.get("current_weather") or {})
        temp = cw.get("temperature")
        wind = cw.get("windspeed")
        code = cw.get("weathercode")
        temp_unit = "°F" if unit_params["temperature_unit"] == "fahrenheit" else "°C"
        wind_unit = "mph" if unit_params["windspeed_unit"] == "mph" else "km/h"

        if temp is None or wind is None or code is None:
            return {"error": f"Weather unavailable for {name}, {country}."}

        desc = _code_desc(int(code))
        loc = f"{name}, {country}".strip().rstrip(',')
        return {
            "location": loc,
            "city": name,
            "country": country,
            "latitude": lat,
            "longitude": lon,
            "temperature": temp,
            "temperature_unit": temp_unit,
            "windspeed": wind,
            "windspeed_unit": wind_unit,
            "description": desc,
            "code": int(code),
        }
    except requests.RequestException as e:
        return {"error": f"Weather lookup failed: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error during weather lookup: {e}"}
