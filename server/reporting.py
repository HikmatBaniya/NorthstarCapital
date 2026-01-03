from __future__ import annotations

import os
from typing import Any, Dict, List

from langchain_groq import ChatGroq


def _table_md(headers: List[str], rows: List[List[Any]]) -> str:
    head = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = "\n".join("| " + " | ".join(str(v) for v in row) + " |" for row in rows)
    return "\n".join([head, sep, body])


def _render_markdown(bundle: Dict[str, Any], narrative: str) -> str:
    quote = bundle.get("quote", {})
    profile = bundle.get("profile", {})
    financials = bundle.get("financials", {})
    filings_raw = bundle.get("filings", {}).get("filings", [])
    news = bundle.get("news", [])
    md = []
    md.append(f"# Research Report: {bundle.get('ticker')}")
    md.append(f"Generated: {bundle.get('generated_at')}")
    md.append("")
    if narrative:
        md.append("## Executive Summary")
        md.append(narrative)
        md.append("")
    md.append("## Quote Snapshot")
    md.append(
        _table_md(
            ["Symbol", "Date", "Open", "High", "Low", "Close", "Volume", "Source"],
            [
                [
                    quote.get("symbol"),
                    quote.get("date"),
                    quote.get("open"),
                    quote.get("high"),
                    quote.get("low"),
                    quote.get("close"),
                    quote.get("volume"),
                    quote.get("source"),
                ]
            ],
        )
    )
    md.append("")
    md.append("## Company Profile")
    md.append(
        _table_md(
            ["Name", "CIK", "SIC", "State", "FY End", "Entity Type"],
            [
                [
                    profile.get("name"),
                    profile.get("cik"),
                    profile.get("sic"),
                    profile.get("state_of_incorporation"),
                    profile.get("fiscal_year_end"),
                    profile.get("entity_type"),
                ]
            ],
        )
    )
    md.append("")
    md.append("## Key Financial Metrics")
    metric_rows = []
    for key, value in financials.get("metrics", {}).items():
        metric_rows.append([key, value.get("value"), value.get("end"), value.get("form")])
    if metric_rows:
        md.append(_table_md(["Metric", "Value", "Period End", "Form"], metric_rows))
    else:
        md.append("No metrics found.")
    md.append("")
    md.append("## Recent Filings")
    filing_rows = []
    for item in filings_raw[:8]:
        filing_rows.append(
            [
                item.get("form"),
                item.get("filing_date"),
                item.get("report_date"),
                item.get("filing_url"),
            ]
        )
    if filing_rows:
        md.append(_table_md(["Form", "Filing Date", "Report Date", "URL"], filing_rows))
    else:
        md.append("No filings found.")
    md.append("")
    md.append("## Recent News")
    news_rows = []
    for item in news[:8]:
        news_rows.append([item.get("title"), item.get("href")])
    if news_rows:
        md.append(_table_md(["Headline", "URL"], news_rows))
    else:
        md.append("No news found.")
    md.append("")
    return "\n".join(md)


def _render_html(markdown: str, data: Dict[str, Any]) -> str:
    title = data.get("ticker", "Report")
    kpis = data.get("kpis", {})
    price = kpis.get("price")
    change = None
    if kpis.get("open") and price is not None:
        change = (price - kpis.get("open")) / kpis.get("open") * 100
    html = markdown.replace("\n\n", "</p><p>")
    html = html.replace("\n", "<br/>")
    return f"""
<html>
<head>
  <style>
    body {{ font-family: Arial, sans-serif; background: #0f162a; color: #e4ecff; padding: 24px; }}
    h1, h2 {{ color: #c5d2ff; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin: 16px 0; }}
    .kpi {{ background: #10182b; padding: 12px; border-radius: 10px; border: 1px solid #1b2a4a; }}
    .kpi .label {{ font-size: 12px; color: #9fb1d9; }}
    .kpi .value {{ font-size: 16px; font-weight: bold; }}
    .pill {{ display: inline-block; padding: 4px 8px; border-radius: 999px; background: #1c2b4a; }}
    a {{ color: #7dd3fc; }}
  </style>
</head>
<body>
  <h1>Research Report: {title}</h1>
  <div class="kpi-grid">
    <div class="kpi"><div class="label">Price</div><div class="value">{price}</div></div>
    <div class="kpi"><div class="label">Open</div><div class="value">{kpis.get("open")}</div></div>
    <div class="kpi"><div class="label">High</div><div class="value">{kpis.get("high")}</div></div>
    <div class="kpi"><div class="label">Low</div><div class="value">{kpis.get("low")}</div></div>
    <div class="kpi"><div class="label">Change %</div><div class="value">{round(change,2) if change is not None else "N/A"}</div></div>
  </div>
  <div class="kpi-grid">
    <div class="kpi"><div class="label">Market Cap</div><div class="value">{kpis.get("market_cap")}</div></div>
    <div class="kpi"><div class="label">P/E</div><div class="value">{kpis.get("pe_ratio")}</div></div>
    <div class="kpi"><div class="label">P/S</div><div class="value">{kpis.get("price_to_sales")}</div></div>
    <div class="kpi"><div class="label">P/B</div><div class="value">{kpis.get("price_to_book")}</div></div>
    <div class="kpi"><div class="label">Beta</div><div class="value">{kpis.get("beta")}</div></div>
  </div>
  <div class="pill">HTML Summary</div>
  <p>{html}</p>
</body>
</html>
"""


def _compact_bundle(bundle: Dict[str, Any], max_news: int, max_filings: int) -> Dict[str, Any]:
    quote = bundle.get("quote", {})
    profile = bundle.get("profile", {})
    financials = bundle.get("financials", {}).get("metrics", {})
    filings = bundle.get("filings", {}).get("filings", [])[:max_filings]
    news = bundle.get("news", [])[:max_news]
    return {
        "ticker": bundle.get("ticker"),
        "quote": {
            "date": quote.get("date"),
            "open": quote.get("open"),
            "high": quote.get("high"),
            "low": quote.get("low"),
            "close": quote.get("close"),
            "volume": quote.get("volume"),
            "source": quote.get("source"),
        },
        "profile": {
            "name": profile.get("name"),
            "cik": profile.get("cik"),
            "sic": profile.get("sic"),
            "state": profile.get("state_of_incorporation"),
            "fiscal_year_end": profile.get("fiscal_year_end"),
            "entity_type": profile.get("entity_type"),
        },
        "metrics": financials,
        "filings": [
            {
                "form": f.get("form"),
                "filing_date": f.get("filing_date"),
                "report_date": f.get("report_date"),
                "url": f.get("filing_url"),
            }
            for f in filings
        ],
        "news": [{"title": n.get("title"), "url": n.get("href")} for n in news],
    }


def _trim_text(text: str, limit: int) -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    return text[:limit]


def _generate_narrative(bundle: Dict[str, Any]) -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return ""
    model = os.getenv("GROQ_REPORT_MODEL", os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
    max_chars = int(os.getenv("REPORT_MAX_INPUT_CHARS", "6000"))
    news_items = int(os.getenv("REPORT_NEWS_ITEMS", "5"))
    filings_items = int(os.getenv("REPORT_FILINGS_ITEMS", "5"))
    compact = _compact_bundle(bundle, news_items, filings_items)
    compact_text = _trim_text(str(compact), max_chars)
    llm = ChatGroq(api_key=api_key, model=model, temperature=0.2)
    prompt = (
        "You are a finance analyst. Summarize the company's situation based on the data. "
        "Highlight revenue, profitability, balance sheet health, and notable filings/news. "
        "Keep it concise (max 8 bullets). Data:\n"
        f"{compact_text}"
    )
    result = llm.invoke(prompt)
    return getattr(result, "content", "") or ""


def generate_report(bundle: Dict[str, Any], use_llm: bool = True) -> Dict[str, str]:
    narrative = _generate_narrative(bundle) if use_llm else ""
    markdown = _render_markdown(bundle, narrative)
    data = _build_report_data(bundle)
    html = _render_html(markdown, data)
    return {"markdown": markdown, "html": html, "data": data}


def _build_report_data(bundle: Dict[str, Any]) -> Dict[str, Any]:
    quote = bundle.get("quote", {})
    history = bundle.get("history", {}).get("data", [])
    financials = bundle.get("financials", {}).get("metrics", {})
    overview = bundle.get("overview", {})
    price_stats = bundle.get("price_stats", {})
    filings_raw = bundle.get("filings", {}).get("filings", [])
    news = bundle.get("news", [])

    price_series = [
        {"date": row.get("date"), "close": row.get("close"), "volume": row.get("volume")}
        for row in history
    ]

    price_change_pct = None
    if quote.get("open") and quote.get("close"):
        price_change_pct = (quote.get("close") - quote.get("open")) / quote.get("open") * 100

    kpis = {
        "price": quote.get("close"),
        "open": quote.get("open"),
        "high": quote.get("high"),
        "low": quote.get("low"),
        "volume": quote.get("volume"),
        "price_change_pct": price_change_pct,
        "revenue": _metric_value(financials, "Revenue"),
        "net_income": _metric_value(financials, "NetIncome"),
        "assets": _metric_value(financials, "Assets"),
        "liabilities": _metric_value(financials, "Liabilities"),
        "cash": _metric_value(financials, "Cash"),
        "pe_ratio": overview.get("pe_ratio"),
        "market_cap": overview.get("market_cap"),
        "beta": overview.get("beta"),
        "price_to_sales": overview.get("price_to_sales"),
        "price_to_book": overview.get("price_to_book"),
    }

    return {
        "ticker": bundle.get("ticker"),
        "generated_at": bundle.get("generated_at"),
        "kpis": kpis,
        "price_stats": price_stats,
        "overview": overview,
        "price_series": price_series,
        "financials": financials,
        "filings": [
            {
                "title": f.get("primary_description") or f.get("primary_document"),
                "link": f.get("filing_url"),
                "date": f.get("filing_date"),
                "type": f.get("form"),
            }
            for f in filings_raw
        ],
        "news": news,
        "quote": quote,
        "data_health": _data_health(bundle),
    }


def _metric_value(financials: Dict[str, Any], key: str) -> Any:
    item = financials.get(key) or {}
    return item.get("value")


def _data_health(bundle: Dict[str, Any]) -> Dict[str, Any]:
    missing = []
    financials = bundle.get("financials", {}).get("metrics", {})
    for key in ["Revenue", "NetIncome", "Assets", "Liabilities", "Cash"]:
        if key not in financials:
            missing.append(key)
    metric_dates = [
        item.get("end")
        for item in financials.values()
        if isinstance(item, dict) and item.get("end")
    ]
    oldest = min(metric_dates) if metric_dates else None
    newest = max(metric_dates) if metric_dates else None
    return {
        "missing_metrics": missing,
        "oldest_metric_date": oldest,
        "newest_metric_date": newest,
        "news_count": len(bundle.get("news", []) or []),
        "filings_count": len(bundle.get("filings", {}).get("filings", []) or []),
    }
