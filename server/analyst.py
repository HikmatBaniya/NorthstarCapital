from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from .config import Settings
from .tools.nepse_tools import nepse_company_details, nepse_price_volume, nepse_live_market


ANALYSIS_SCHEMA = {
    "facts": [{"text": "", "sources": ["source_id"]}],
    "signals": [{"text": "", "sources": ["source_id"]}],
    "thesis": [""],
    "risks": [""],
    "scenarios": {"bull": "", "base": "", "bear": ""},
    "uncertainty": [""],
    "disclaimer": "",
}

MAX_FACTS = 40
MAX_SIGNALS = 20
MAX_SOURCES = 12
MAX_MISSING = 10


MARKET_RULES = {
    "NEPSE": [
        "Liquidity is uneven; emphasize trade volume and spread risk.",
        "Daily price limits (circuit breakers) can distort short-term signals.",
        "Retail participation is high; momentum can be news-driven.",
    ],
}


def _source_entry(source_id: str, label: str, url: str | None = None) -> Dict[str, Any]:
    return {"id": source_id, "label": label, "url": url}


def _add_fact(
    facts: List[Dict[str, Any]],
    label: str,
    value: Any,
    source_id: str,
    unit: str | None = None,
) -> None:
    if value is None:
        return
    facts.append(
        {
            "label": label,
            "value": value,
            "unit": unit,
            "source_id": source_id,
        }
    )


def _brief_nepse(settings: Settings, symbol: str) -> Dict[str, Any]:
    sources = [
        _source_entry("nepse_company_details", "NEPSE CompanyDetails"),
        _source_entry("nepse_price_volume", "NEPSE PriceVolume"),
        _source_entry("nepse_live_market", "NEPSE LiveMarket"),
    ]

    details = nepse_company_details(settings, symbol)
    price_volume = nepse_price_volume(settings)
    live_market = nepse_live_market(settings)
    price_row = next((row for row in price_volume if row.get("symbol") == symbol), {})
    live_row = next((row for row in live_market if row.get("symbol") == symbol), {})
    daily = details.get("securityDailyTradeDto") or {}

    facts: List[Dict[str, Any]] = []
    _add_fact(facts, "Company Name", details.get("companyName"), "nepse_company_details")
    _add_fact(facts, "Sector", details.get("sectorName"), "nepse_company_details")
    _add_fact(facts, "Instrument Type", details.get("instrumentType"), "nepse_company_details")
    _add_fact(facts, "Last Traded Price", price_row.get("lastTradedPrice"), "nepse_price_volume", "NPR")
    _add_fact(facts, "Previous Close", price_row.get("previousClose"), "nepse_price_volume", "NPR")
    _add_fact(facts, "Close Price", price_row.get("closePrice"), "nepse_price_volume", "NPR")
    _add_fact(facts, "Total Trade Quantity", price_row.get("totalTradeQuantity"), "nepse_price_volume")
    _add_fact(facts, "Percentage Change", price_row.get("percentageChange"), "nepse_price_volume", "%")
    _add_fact(facts, "Daily Open", daily.get("openPrice"), "nepse_company_details", "NPR")
    _add_fact(facts, "Daily High", daily.get("highPrice"), "nepse_company_details", "NPR")
    _add_fact(facts, "Daily Low", daily.get("lowPrice"), "nepse_company_details", "NPR")
    _add_fact(facts, "Total Trades", daily.get("totalTrades"), "nepse_company_details")
    _add_fact(facts, "Market Capitalization", details.get("marketCapitalization"), "nepse_company_details", "NPR")
    _add_fact(facts, "Paid Up Capital", details.get("paidUpCapital"), "nepse_company_details", "NPR")
    _add_fact(facts, "Public Percentage", details.get("publicPercentage"), "nepse_company_details", "%")
    _add_fact(facts, "Promoter Shares", details.get("promoterShares"), "nepse_company_details")

    signals: List[Dict[str, Any]] = []
    change_pct = price_row.get("percentageChange")
    if change_pct is not None:
        signals.append(
            {
                "label": "Daily % Change",
                "value": change_pct,
                "method": "NEPSE PriceVolume percentageChange",
                "source_id": "nepse_price_volume",
            }
        )
    live_change = live_row.get("percentageChange")
    if live_change is not None:
        signals.append(
            {
                "label": "Live % Change",
                "value": live_change,
                "method": "NEPSE LiveMarket percentageChange",
                "source_id": "nepse_live_market",
            }
        )

    missing = []
    missing_required = []
    required_sources = ["nepse_company_details", "nepse_price_volume"]
    if not price_row:
        missing.append("PriceVolume data missing for symbol")
        missing_required.append("nepse_price_volume")
    if not details:
        missing.append("CompanyDetails missing for symbol")
        missing_required.append("nepse_company_details")

    return {
        "market": "NEPSE",
        "symbol": symbol,
        "as_of": datetime.utcnow().isoformat() + "Z",
        "sources": sources,
        "required_sources": required_sources,
        "missing_required": missing_required,
        "facts": facts,
        "signals": signals,
        "missing": missing,
        "raw": {
            "company_details": details,
            "price_volume": price_row,
            "live_market": live_row,
        },
    }


def build_brief(settings: Settings, market: str, symbol: str, horizon_days: int) -> Dict[str, Any]:
    market_upper = market.upper()
    if market_upper == "NEPSE":
        return _brief_nepse(settings, symbol)
    raise ValueError("unsupported_market")


def _compact_brief(brief: Dict[str, Any]) -> Dict[str, Any]:
    compact = dict(brief)
    compact["facts"] = list(brief.get("facts", []))[:MAX_FACTS]
    compact["signals"] = list(brief.get("signals", []))[:MAX_SIGNALS]
    compact["sources"] = list(brief.get("sources", []))[:MAX_SOURCES]
    compact["missing"] = list(brief.get("missing", []))[:MAX_MISSING]
    compact["missing_required"] = list(brief.get("missing_required", []))[:MAX_MISSING]
    # Raw blobs can explode token usage; drop by default.
    compact.pop("raw", None)
    return compact


def generate_analysis(
    settings: Settings,
    brief: Dict[str, Any],
    include_disclaimer: bool = True,
    model_override: str | None = None,
) -> Dict[str, Any]:
    rules = MARKET_RULES.get(brief.get("market", ""), [])
    brief = _compact_brief(brief)
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model=model_override or settings.groq_model,
        temperature=min(settings.groq_temperature, 0.3),
    )

    system_prompt = (
        "You are a structured equity research analyst. "
        "You MUST return valid JSON only, matching the provided schema. "
        "All numeric or factual claims must map to brief.facts or brief.signals. "
        "Use sources by referencing source_id arrays for facts/signals. "
        "If key data is missing, list it under uncertainty and keep thesis tentative. "
        "Avoid investment advice. Use neutral language like 'could' or 'may'."
    )
    if rules:
        system_prompt += "\nMarket rules:\n- " + "\n- ".join(rules)

    prompt = (
        "Brief JSON:\n"
        f"{json.dumps(brief, ensure_ascii=False)}\n\n"
        "Return JSON with keys: facts, signals, thesis, risks, scenarios, uncertainty, disclaimer.\n"
        f"Schema example:\n{json.dumps(ANALYSIS_SCHEMA, ensure_ascii=False)}"
    )

    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=prompt)])
    content = response.content if isinstance(response.content, str) else str(response.content)
    parsed = _parse_json_response(content)

    if include_disclaimer and isinstance(parsed, dict):
        parsed.setdefault(
            "disclaimer",
            "This analysis is informational only and not investment advice.",
        )
    return parsed


def validate_analysis(brief: Dict[str, Any], analysis: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not isinstance(analysis, dict):
        return False, ["analysis_not_object"]
    for key in ("facts", "signals", "thesis", "risks", "scenarios", "uncertainty", "disclaimer"):
        if key not in analysis:
            errors.append(f"missing_{key}")
    source_ids = {src.get("id") for src in brief.get("sources", [])}
    for section_key in ("facts", "signals"):
        for item in analysis.get(section_key, []) or []:
            sources = item.get("sources") if isinstance(item, dict) else []
            if not sources:
                errors.append(f"{section_key}_missing_sources")
                continue
            for src in sources:
                if src not in source_ids:
                    errors.append(f"{section_key}_unknown_source:{src}")
    return len(errors) == 0, errors


def _parse_json_response(content: str) -> Dict[str, Any]:
    text = content.strip()
    # Strip common code fences
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract the first JSON object block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start : end + 1]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            pass

    # Fallback to a valid schema with uncertainty
    return {
        "facts": [],
        "signals": [],
        "thesis": [],
        "risks": [],
        "scenarios": {"bull": "", "base": "", "bear": ""},
        "uncertainty": [
            "Model output was not valid JSON. Please retry the request.",
        ],
        "disclaimer": "This analysis is informational only and not investment advice.",
        "raw": content,
    }
