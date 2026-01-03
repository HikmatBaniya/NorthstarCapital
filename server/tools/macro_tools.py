from __future__ import annotations

from typing import Any, Dict, List

from ..config import Settings
from ..http_client import http_get


def macro_series(settings: Settings, series_id: str) -> Dict[str, Any]:
    parts = series_id.replace("/", ":").split(":")
    if len(parts) != 2:
        return {"series_id": series_id, "error": "use INDICATOR:COUNTRY (e.g., NY.GDP.MKTP.CD:US)"}
    indicator, country = parts[0], parts[1]
    url = (
        "https://api.worldbank.org/v2/country/"
        f"{country}/indicator/{indicator}?format=json"
    )
    response = http_get(settings, url, cache_ttl=300)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list) or len(data) < 2:
        return {"series_id": series_id, "data": [], "source": "worldbank"}
    items = data[1]
    rows: List[Dict[str, Any]] = []
    for item in items[:20]:
        rows.append(
            {
                "date": item.get("date"),
                "value": item.get("value"),
                "country": item.get("country", {}).get("value"),
                "indicator": item.get("indicator", {}).get("value"),
            }
        )
    return {"series_id": series_id, "data": rows, "source": "worldbank"}
