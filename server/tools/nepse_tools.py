from __future__ import annotations

from typing import Any, Dict, List

from ..config import Settings
from ..http_client import http_get


def _nepse_url(settings: Settings, path: str) -> str:
    base = settings.nepse_api_base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}{path}"


def nepse_company_details(settings: Settings, symbol: str) -> Dict[str, Any]:
    url = _nepse_url(settings, "/CompanyDetails")
    response = http_get(settings, url, params={"symbol": symbol}, cache_ttl=60)
    response.raise_for_status()
    return response.json()


def nepse_price_volume(settings: Settings) -> List[Dict[str, Any]]:
    url = _nepse_url(settings, "/PriceVolume")
    response = http_get(settings, url, cache_ttl=30)
    response.raise_for_status()
    return response.json()


def nepse_live_market(settings: Settings) -> List[Dict[str, Any]]:
    url = _nepse_url(settings, "/LiveMarket")
    response = http_get(settings, url, cache_ttl=15)
    response.raise_for_status()
    return response.json()


def nepse_symbol_snapshot(settings: Settings, symbol: str) -> Dict[str, Any]:
    symbol_upper = symbol.strip().upper()
    live = nepse_live_market(settings)
    live_row = next((row for row in live if row.get("symbol") == symbol_upper), {})
    price_volume = nepse_price_volume(settings)
    price_row = next((row for row in price_volume if row.get("symbol") == symbol_upper), {})
    details = nepse_company_details(settings, symbol_upper)
    daily = details.get("securityDailyTradeDto") or {}
    return {
        "symbol": symbol_upper,
        "companyName": details.get("companyName"),
        "sectorName": details.get("sectorName"),
        "instrumentType": details.get("instrumentType"),
        "lastTradedPrice": live_row.get("lastTradedPrice") or price_row.get("lastTradedPrice"),
        "previousClose": price_row.get("previousClose"),
        "percentageChange": live_row.get("percentageChange") or price_row.get("percentageChange"),
        "openPrice": daily.get("openPrice"),
        "highPrice": daily.get("highPrice"),
        "lowPrice": daily.get("lowPrice"),
        "totalTrades": daily.get("totalTrades"),
        "totalTradeQuantity": price_row.get("totalTradeQuantity") or daily.get("totalTradeQuantity"),
    }


def nepse_summary(settings: Settings) -> Dict[str, Any]:
    url = _nepse_url(settings, "/Summary")
    response = http_get(settings, url, cache_ttl=30)
    response.raise_for_status()
    return response.json()


def nepse_index(settings: Settings) -> Dict[str, Any]:
    url = _nepse_url(settings, "/NepseIndex")
    response = http_get(settings, url, cache_ttl=30)
    response.raise_for_status()
    return response.json()


def nepse_subindices(settings: Settings) -> Dict[str, Any]:
    url = _nepse_url(settings, "/NepseSubIndices")
    response = http_get(settings, url, cache_ttl=30)
    response.raise_for_status()
    return response.json()


def nepse_is_open(settings: Settings) -> Dict[str, Any]:
    url = _nepse_url(settings, "/IsNepseOpen")
    response = http_get(settings, url, cache_ttl=15)
    response.raise_for_status()
    return response.json()


def nepse_top_gainers(settings: Settings) -> List[Dict[str, Any]]:
    url = _nepse_url(settings, "/TopGainers")
    response = http_get(settings, url, cache_ttl=30)
    response.raise_for_status()
    return response.json()


def nepse_top_losers(settings: Settings) -> List[Dict[str, Any]]:
    url = _nepse_url(settings, "/TopLosers")
    response = http_get(settings, url, cache_ttl=30)
    response.raise_for_status()
    return response.json()


def nepse_top_trade_scrips(settings: Settings) -> List[Dict[str, Any]]:
    url = _nepse_url(settings, "/TopTenTradeScrips")
    response = http_get(settings, url, cache_ttl=30)
    response.raise_for_status()
    return response.json()


def nepse_top_transaction_scrips(settings: Settings) -> List[Dict[str, Any]]:
    url = _nepse_url(settings, "/TopTenTransactionScrips")
    response = http_get(settings, url, cache_ttl=30)
    response.raise_for_status()
    return response.json()


def nepse_top_turnover_scrips(settings: Settings) -> List[Dict[str, Any]]:
    url = _nepse_url(settings, "/TopTenTurnoverScrips")
    response = http_get(settings, url, cache_ttl=30)
    response.raise_for_status()
    return response.json()


def nepse_supply_demand(settings: Settings) -> Dict[str, Any]:
    url = _nepse_url(settings, "/SupplyDemand")
    response = http_get(settings, url, cache_ttl=30)
    response.raise_for_status()
    return response.json()


def nepse_trade_turnover_transaction(settings: Settings) -> Dict[str, Any]:
    url = _nepse_url(settings, "/TradeTurnoverTransactionSubindices")
    response = http_get(settings, url, cache_ttl=30)
    response.raise_for_status()
    return response.json()


def nepse_company_list(settings: Settings) -> List[Dict[str, Any]]:
    url = _nepse_url(settings, "/CompanyList")
    response = http_get(settings, url, cache_ttl=300)
    response.raise_for_status()
    return response.json()


def nepse_sector_scrips(settings: Settings) -> Dict[str, Any]:
    url = _nepse_url(settings, "/SectorScrips")
    response = http_get(settings, url, cache_ttl=300)
    response.raise_for_status()
    return response.json()


def nepse_security_list(settings: Settings) -> List[Dict[str, Any]]:
    url = _nepse_url(settings, "/SecurityList")
    response = http_get(settings, url, cache_ttl=300)
    response.raise_for_status()
    return response.json()


def nepse_price_volume_history(settings: Settings, symbol: str) -> List[Dict[str, Any]]:
    url = _nepse_url(settings, "/PriceVolumeHistory")
    response = http_get(settings, url, params={"symbol": symbol}, cache_ttl=60)
    response.raise_for_status()
    return response.json()


def nepse_floorsheet(settings: Settings) -> List[Dict[str, Any]]:
    url = _nepse_url(settings, "/Floorsheet")
    response = http_get(settings, url, cache_ttl=30)
    response.raise_for_status()
    return response.json()


def nepse_floorsheet_of(settings: Settings, symbol: str) -> List[Dict[str, Any]]:
    url = _nepse_url(settings, "/FloorsheetOf")
    response = http_get(settings, url, params={"symbol": symbol}, cache_ttl=30)
    response.raise_for_status()
    return response.json()


def nepse_daily_scrip_price_graph(settings: Settings, symbol: str) -> List[Dict[str, Any]]:
    url = _nepse_url(settings, "/DailyScripPriceGraph")
    response = http_get(settings, url, params={"symbol": symbol}, cache_ttl=60)
    response.raise_for_status()
    return response.json()


def nepse_daily_index_graph(settings: Settings, kind: str) -> List[Any]:
    mapping = {
        "nepse": "/DailyNepseIndexGraph",
        "sensitive": "/DailySensitiveIndexGraph",
        "float": "/DailyFloatIndexGraph",
        "sensitive_float": "/DailySensitiveFloatIndexGraph",
        "bank": "/DailyBankSubindexGraph",
        "development_bank": "/DailyDevelopmentBankSubindexGraph",
        "finance": "/DailyFinanceSubindexGraph",
        "hotel_tourism": "/DailyHotelTourismSubindexGraph",
        "hydro": "/DailyHydroPowerSubindexGraph",
        "investment": "/DailyInvestmentSubindexGraph",
        "life_insurance": "/DailyLifeInsuranceSubindexGraph",
        "manufacturing": "/DailyManufacturingProcessingSubindexGraph",
        "microfinance": "/DailyMicrofinanceSubindexGraph",
        "mutual_fund": "/DailyMutualFundSubindexGraph",
        "non_life_insurance": "/DailyNonLifeInsuranceSubindexGraph",
        "others": "/DailyOthersSubindexGraph",
        "trading": "/DailyTradingSubindexGraph",
    }
    key = kind.strip().lower()
    path = mapping.get(key)
    if not path:
        raise ValueError("unknown_index_kind")
    url = _nepse_url(settings, path)
    response = http_get(settings, url, cache_ttl=60)
    response.raise_for_status()
    return response.json()
