from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..config import Settings
from ..http_client import http_get

_MISSING_NUMERIC = {"", "N/A", "N/D", "NA", "ND", "-", None}


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, str):
        cleaned = value.strip().upper()
        if cleaned in _MISSING_NUMERIC:
            return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    return int(_safe_float(value, float(default)))


def _normalize_stooq_symbol(symbol: str) -> str:
    symbol = symbol.strip().lower()
    if "." in symbol:
        return symbol
    return f"{symbol}.us"


def market_quote(settings: Settings, symbol: str) -> Dict[str, Any]:
    symbol = _normalize_stooq_symbol(symbol)
    url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"
    response = http_get(settings, url, cache_ttl=60)
    response.raise_for_status()
    lines = response.text.strip().splitlines()
    if len(lines) < 2:
        return {"symbol": symbol, "error": "no_data"}
    headers = lines[0].split(",")
    values = lines[1].split(",")
    if "N/A" in values or "N/D" in values:
        return {"symbol": symbol, "error": "no_data"}
    data = dict(zip(headers, values))
    result = {
        "symbol": data.get("Symbol", symbol),
        "date": data.get("Date"),
        "time": data.get("Time"),
        "open": _safe_float(data.get("Open", 0)),
        "high": _safe_float(data.get("High", 0)),
        "low": _safe_float(data.get("Low", 0)),
        "close": _safe_float(data.get("Close", 0)),
        "volume": _safe_int(data.get("Volume", 0)),
        "source": "stooq",
    }
    if result["close"] == 0 and settings.alpha_vantage_api_key:
        return _alpha_quote(settings, symbol.replace(".us", ""))
    return result


def market_history(
    settings: Settings,
    symbol: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 500,
) -> Dict[str, Any]:
    symbol = _normalize_stooq_symbol(symbol)
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    response = http_get(settings, url, cache_ttl=300)
    response.raise_for_status()
    lines = response.text.strip().splitlines()
    if len(lines) < 2:
        return {"symbol": symbol, "data": [], "source": "stooq"}
    headers = lines[0].split(",")
    rows: List[Dict[str, Any]] = []
    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) != len(headers):
            continue
        row = dict(zip(headers, parts))
        date_str = row.get("Date")
        if not date_str:
            continue
        if start and date_str < start:
            continue
        if end and date_str > end:
            continue
        rows.append(
            {
                "date": date_str,
                "open": _safe_float(row.get("Open", 0)),
                "high": _safe_float(row.get("High", 0)),
                "low": _safe_float(row.get("Low", 0)),
                "close": _safe_float(row.get("Close", 0)),
                "volume": _safe_int(row.get("Volume", 0)),
            }
        )
    if limit > 0:
        rows = rows[-limit:]
    result = {"symbol": symbol, "data": rows, "source": "stooq"}
    if not rows and settings.alpha_vantage_api_key:
        return _alpha_history(settings, symbol.replace(".us", ""), start, end, limit)
    return result


def market_fx(settings: Settings, pair: str) -> Dict[str, Any]:
    cleaned = pair.replace("/", "").upper()
    if len(cleaned) != 6:
        return {"pair": pair, "error": "invalid_pair"}
    base = cleaned[:3]
    quote = cleaned[3:]
    url = f"https://open.er-api.com/v6/latest/{base}"
    response = http_get(settings, url, cache_ttl=300)
    response.raise_for_status()
    data = response.json()
    rates = data.get("rates", {})
    rate = rates.get(quote)
    if rate is None:
        return {"pair": pair, "error": "rate_not_found"}
    return {
        "pair": f"{base}/{quote}",
        "rate": rate,
        "time_last_update_utc": data.get("time_last_update_utc"),
        "source": "open.er-api.com",
    }


_COINGECKO_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "ADA": "cardano",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "USDT": "tether",
    "BNB": "binancecoin",
}


def market_crypto(settings: Settings, symbol: str, vs_currency: str = "usd") -> Dict[str, Any]:
    sym = symbol.strip().upper()
    coin_id = _COINGECKO_MAP.get(sym)
    if not coin_id:
        return {"symbol": sym, "error": "unsupported_symbol"}
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        f"?ids={coin_id}&vs_currencies={vs_currency}"
    )
    response = http_get(settings, url, cache_ttl=120)
    response.raise_for_status()
    data = response.json()
    price = data.get(coin_id, {}).get(vs_currency)
    if price is None:
        return {"symbol": sym, "error": "price_not_found"}
    return {"symbol": sym, "price": price, "vs_currency": vs_currency, "source": "coingecko"}


def _alpha_quote(settings: Settings, symbol: str) -> Dict[str, Any]:
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": settings.alpha_vantage_api_key,
    }
    response = http_get(settings, url, params=params, cache_ttl=60)
    response.raise_for_status()
    data = response.json().get("Global Quote", {})
    price = _safe_float(data.get("05. price", 0))
    volume = _safe_int(data.get("06. volume", 0))
    return {
        "symbol": data.get("01. symbol", symbol),
        "date": data.get("07. latest trading day"),
        "time": None,
        "open": _safe_float(data.get("02. open", 0)),
        "high": _safe_float(data.get("03. high", 0)),
        "low": _safe_float(data.get("04. low", 0)),
        "close": price,
        "volume": volume,
        "source": "alpha_vantage",
    }


def _alpha_history(
    settings: Settings,
    symbol: str,
    start: Optional[str],
    end: Optional[str],
    limit: int,
) -> Dict[str, Any]:
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": settings.alpha_vantage_api_key,
    }
    response = http_get(settings, url, params=params, cache_ttl=300)
    response.raise_for_status()
    data = response.json().get("Time Series (Daily)", {})
    rows: List[Dict[str, Any]] = []
    for date_str, values in sorted(data.items()):
        if start and date_str < start:
            continue
        if end and date_str > end:
            continue
        rows.append(
            {
                "date": date_str,
                "open": _safe_float(values.get("1. open", 0)),
                "high": _safe_float(values.get("2. high", 0)),
                "low": _safe_float(values.get("3. low", 0)),
                "close": _safe_float(values.get("4. close", 0)),
                "volume": _safe_int(values.get("6. volume", 0)),
            }
        )
    if limit > 0:
        rows = rows[-limit:]
    return {"symbol": symbol, "data": rows, "source": "alpha_vantage"}
