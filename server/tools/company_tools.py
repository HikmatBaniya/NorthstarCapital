from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..config import Settings
from ..http_client import http_get
from .sec_tools import _cik_from_query


def company_profile(settings: Settings, ticker: str) -> Dict[str, Any]:
    cik = _cik_from_query(settings, ticker)
    if not cik:
        return {"ticker": ticker, "error": "ticker_or_cik_not_found"}
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {"User-Agent": settings.sec_user_agent or settings.user_agent}
    response = http_get(settings, url, headers=headers, cache_ttl=300)
    response.raise_for_status()
    data = response.json()
    return {
        "cik": cik,
        "name": data.get("name"),
        "tickers": data.get("tickers"),
        "sic": data.get("sic"),
        "sic_description": data.get("sicDescription"),
        "state_of_incorporation": data.get("stateOfIncorporation"),
        "fiscal_year_end": data.get("fiscalYearEnd"),
        "entity_type": data.get("entityType"),
        "insider_transaction_for_owner_exists": data.get("insiderTransactionForOwnerExists"),
        "insider_transaction_for_issuer_exists": data.get("insiderTransactionForIssuerExists"),
        "source": "sec",
    }


def _latest_usd_fact(fact: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    units = fact.get("units", {}).get("USD", [])
    if not units:
        return None
    latest = None
    for item in units:
        if not latest or (item.get("end") or "") > (latest.get("end") or ""):
            latest = item
    return latest


def company_financials(settings: Settings, ticker: str) -> Dict[str, Any]:
    cik = _cik_from_query(settings, ticker)
    if not cik:
        return {"ticker": ticker, "error": "ticker_or_cik_not_found"}
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    headers = {"User-Agent": settings.sec_user_agent or settings.user_agent}
    response = http_get(settings, url, headers=headers, cache_ttl=300)
    response.raise_for_status()
    data = response.json()
    facts = data.get("facts", {}).get("us-gaap", {})

    metrics = {
        "Revenue": facts.get("Revenues"),
        "NetIncome": facts.get("NetIncomeLoss"),
        "Assets": facts.get("Assets"),
        "Liabilities": facts.get("Liabilities"),
        "Cash": facts.get("CashAndCashEquivalentsAtCarryingValue"),
    }
    extracted: Dict[str, Any] = {}
    for label, fact in metrics.items():
        if not fact:
            continue
        latest = _latest_usd_fact(fact)
        if not latest:
            continue
        extracted[label] = {
            "value": latest.get("val"),
            "end": latest.get("end"),
            "form": latest.get("form"),
            "fy": latest.get("fy"),
            "fp": latest.get("fp"),
        }

    return {
        "cik": cik,
        "name": data.get("entityName"),
        "ticker": ticker,
        "metrics": extracted,
        "source": "sec_xbrl",
    }


def company_overview(settings: Settings, ticker: str) -> Dict[str, Any]:
    if not settings.alpha_vantage_api_key:
        return {"ticker": ticker, "error": "alpha_vantage_key_missing"}
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "OVERVIEW",
        "symbol": ticker,
        "apikey": settings.alpha_vantage_api_key,
    }
    response = http_get(settings, url, params=params, cache_ttl=86400)
    response.raise_for_status()
    data = response.json()
    if not data or "Symbol" not in data:
        return {"ticker": ticker, "error": "overview_not_found"}
    return {
        "ticker": data.get("Symbol"),
        "market_cap": data.get("MarketCapitalization"),
        "pe_ratio": data.get("PERatio"),
        "pe_forward": data.get("ForwardPE"),
        "peg_ratio": data.get("PEGRatio"),
        "price_to_sales": data.get("PriceToSalesRatioTTM"),
        "price_to_book": data.get("PriceToBookRatio"),
        "dividend_yield": data.get("DividendYield"),
        "profit_margin": data.get("ProfitMargin"),
        "operating_margin": data.get("OperatingMarginTTM"),
        "roe": data.get("ReturnOnEquityTTM"),
        "roa": data.get("ReturnOnAssetsTTM"),
        "beta": data.get("Beta"),
        "analyst_target_price": data.get("AnalystTargetPrice"),
        "source": "alpha_vantage",
    }
