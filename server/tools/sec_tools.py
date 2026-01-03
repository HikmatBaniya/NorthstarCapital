from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from ..config import Settings
from ..http_client import http_get


def _normalize_cik(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits.zfill(10)


@lru_cache(maxsize=1)
def _ticker_map(settings: Settings) -> Dict[str, str]:
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": settings.sec_user_agent or settings.user_agent}
    response = http_get(settings, url, headers=headers, cache_ttl=86400)
    response.raise_for_status()
    data = response.json()
    mapping: Dict[str, str] = {}
    for _, item in data.items():
        ticker = str(item.get("ticker", "")).upper()
        cik = str(item.get("cik_str", ""))
        if ticker and cik:
            mapping[ticker] = cik
    return mapping


def _cik_from_query(settings: Settings, query: str) -> Optional[str]:
    query = query.strip()
    if not query:
        return None
    if query.isdigit():
        return _normalize_cik(query)
    if query.upper().startswith("CIK"):
        return _normalize_cik(query[3:])
    mapping = _ticker_map(settings)
    cik = mapping.get(query.upper())
    return _normalize_cik(cik) if cik else None


def sec_search(settings: Settings, query: str, limit: int = 20) -> Dict[str, Any]:
    cik = _cik_from_query(settings, query)
    if not cik:
        return {"query": query, "error": "ticker_or_cik_not_found"}
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {"User-Agent": settings.sec_user_agent or settings.user_agent}
    response = http_get(settings, url, headers=headers, cache_ttl=300)
    response.raise_for_status()
    data = response.json()
    filings = data.get("filings", {}).get("recent", {})
    accession = filings.get("accessionNumber", [])
    forms = filings.get("form", [])
    filing_dates = filings.get("filingDate", [])
    report_dates = filings.get("reportDate", [])
    primary_docs = filings.get("primaryDocument", [])
    primary_desc = filings.get("primaryDocDescription", [])
    rows: List[Dict[str, Any]] = []
    for idx in range(min(len(accession), limit)):
        acc = accession[idx]
        acc_no_dash = acc.replace("-", "")
        doc = primary_docs[idx] if idx < len(primary_docs) else ""
        filing_url = ""
        if doc:
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no_dash}/{doc}"
        rows.append(
            {
                "accession": acc,
                "form": forms[idx] if idx < len(forms) else None,
                "filing_date": filing_dates[idx] if idx < len(filing_dates) else None,
                "report_date": report_dates[idx] if idx < len(report_dates) else None,
                "primary_document": doc,
                "primary_description": primary_desc[idx] if idx < len(primary_desc) else None,
                "filing_url": filing_url,
            }
        )
    return {
        "query": query,
        "cik": cik,
        "company_name": data.get("name"),
        "tickers": data.get("tickers"),
        "filings": rows,
        "source": "sec",
    }


def sec_filing(settings: Settings, url: str) -> Dict[str, Any]:
    headers = {"User-Agent": settings.sec_user_agent or settings.user_agent}
    response = http_get(settings, url, headers=headers, cache_ttl=300)
    response.raise_for_status()
    text = response.text
    soup = BeautifulSoup(text, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    clean_text = " ".join(soup.get_text(separator=" ").split())
    return {
        "url": response.url,
        "status_code": response.status_code,
        "text": clean_text[:200000],
    }


def sec_company_facts(settings: Settings, query: str) -> Dict[str, Any]:
    cik = _cik_from_query(settings, query)
    if not cik:
        return {"query": query, "error": "ticker_or_cik_not_found"}
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    headers = {"User-Agent": settings.sec_user_agent or settings.user_agent}
    response = http_get(settings, url, headers=headers, cache_ttl=86400)
    response.raise_for_status()
    payload = response.json()
    return {
        "query": query,
        "cik": cik,
        "company_name": payload.get("entityName"),
        "facts": payload.get("facts", {}),
        "source": "sec",
    }
