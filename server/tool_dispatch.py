from __future__ import annotations

from typing import Any, Dict, List

from .config import Settings
from .db import memory_put, memory_search
from .tool_registry import TOOLS
from .tools.calc_tools import calc_portfolio, calc_returns, calc_risk
from .tools.company_tools import company_financials, company_profile
from .tools.macro_tools import macro_series
from .tools.market_tools import market_crypto, market_fx, market_history, market_quote
from .tools.news_tools import news_search
from .tools.sec_tools import sec_filing, sec_search
from .tools.sentiment_tools import sentiment_analyze
from .research import build_research_bundle
from .reporting import generate_report
from .analytics import compare_prices, portfolio_stats
from .tools.web_tools import web_extract, web_fetch, web_fetch_browser, web_search
from .extensions import get_extension


def dispatch_tool(settings: Settings, name: str, arguments: Dict[str, Any]) -> Any:
    tool_names = {t.name for t in TOOLS}
    if name not in tool_names:
        raise KeyError(f"Unknown tool: {name}")

    if name == "web.search":
        query = str(arguments.get("query", "")).strip()
        if not query:
            raise ValueError("query is required")
        return web_search(settings, query)
    if name == "web.fetch":
        url = str(arguments.get("url", "")).strip()
        if not url:
            raise ValueError("url is required")
        headers = arguments.get("headers")
        if headers is not None and not isinstance(headers, dict):
            raise ValueError("headers must be an object")
        return web_fetch(settings, url, headers=headers)
    if name == "web.fetch_browser":
        url = str(arguments.get("url", "")).strip()
        if not url:
            raise ValueError("url is required")
        headers = arguments.get("headers")
        if headers is not None and not isinstance(headers, dict):
            raise ValueError("headers must be an object")
        return web_fetch_browser(settings, url, headers=headers)
    if name == "web.extract":
        html = str(arguments.get("html", ""))
        if not html:
            raise ValueError("html is required")
        return web_extract(settings, html)
    if name == "news.search":
        query = str(arguments.get("query", "")).strip()
        if not query:
            raise ValueError("query is required")
        max_results = int(arguments.get("max_results", 8))
        return news_search(settings, query, max_results)
    if name == "news.extract":
        url = str(arguments.get("url", "")).strip()
        if not url:
            raise ValueError("url is required")
        fetched = web_fetch(settings, url)
        return web_extract(settings, fetched.get("text", ""))
    if name == "market.quote":
        symbol = str(arguments.get("symbol", "")).strip()
        if not symbol:
            raise ValueError("symbol is required")
        return market_quote(settings, symbol)
    if name == "market.history":
        symbol = str(arguments.get("symbol", "")).strip()
        if not symbol:
            raise ValueError("symbol is required")
        start = arguments.get("start")
        end = arguments.get("end")
        limit = int(arguments.get("limit", 500))
        return market_history(settings, symbol, start, end, limit)
    if name == "market.fx":
        pair = str(arguments.get("pair", "")).strip()
        if not pair:
            raise ValueError("pair is required")
        return market_fx(settings, pair)
    if name == "market.crypto":
        symbol = str(arguments.get("symbol", "")).strip()
        if not symbol:
            raise ValueError("symbol is required")
        vs_currency = str(arguments.get("vs_currency", "usd")).strip() or "usd"
        return market_crypto(settings, symbol, vs_currency)
    if name == "company.profile":
        ticker = str(arguments.get("ticker", "")).strip()
        if not ticker:
            raise ValueError("ticker is required")
        return company_profile(settings, ticker)
    if name == "company.financials":
        ticker = str(arguments.get("ticker", "")).strip()
        if not ticker:
            raise ValueError("ticker is required")
        return company_financials(settings, ticker)
    if name == "sec.search":
        query = str(arguments.get("query", "")).strip()
        if not query:
            raise ValueError("query is required")
        limit = int(arguments.get("limit", 20))
        return sec_search(settings, query, limit)
    if name == "sec.filing":
        url = str(arguments.get("url", "")).strip()
        if not url:
            raise ValueError("url is required")
        return sec_filing(settings, url)
    if name == "macro.series":
        series_id = str(arguments.get("series_id", "")).strip()
        if not series_id:
            raise ValueError("series_id is required")
        return macro_series(settings, series_id)
    if name == "sentiment.analyze":
        text = str(arguments.get("text", "")).strip()
        if not text:
            raise ValueError("text is required")
        return sentiment_analyze(text)
    if name == "calc.returns":
        prices = arguments.get("prices") or []
        if not isinstance(prices, list):
            raise ValueError("prices must be a list")
        return calc_returns(prices)
    if name == "calc.risk":
        returns = arguments.get("returns") or []
        if not isinstance(returns, list):
            raise ValueError("returns must be a list")
        return calc_risk(returns)
    if name == "calc.portfolio":
        weights = arguments.get("weights") or []
        if not isinstance(weights, list):
            raise ValueError("weights must be a list")
        return calc_portfolio(weights)
    if name == "memory.put":
        content = str(arguments.get("content", "")).strip()
        if not content:
            raise ValueError("content is required")
        tags = arguments.get("tags") or []
        if not isinstance(tags, list):
            raise ValueError("tags must be a list")
        conversation_id = arguments.get("conversation_id")
        return memory_put(content, tags, conversation_id=conversation_id)
    if name == "memory.search":
        query = str(arguments.get("query", "")).strip()
        if not query:
            raise ValueError("query is required")
        limit = int(arguments.get("limit", 8))
        if limit <= 0:
            limit = 8
        conversation_id = arguments.get("conversation_id")
        return memory_search(query, limit, conversation_id=conversation_id)
    if name == "research.bundle":
        ticker = str(arguments.get("ticker", "")).strip()
        if not ticker:
            raise ValueError("ticker is required")
        horizon_days = int(arguments.get("horizon_days", 365))
        news_limit = int(arguments.get("news_limit", 6))
        filings_limit = int(arguments.get("filings_limit", 5))
        return build_research_bundle(
            settings,
            ticker,
            horizon_days=horizon_days,
            news_limit=news_limit,
            filings_limit=filings_limit,
        )
    if name == "report.generate":
        ticker = str(arguments.get("ticker", "")).strip()
        if not ticker:
            raise ValueError("ticker is required")
        use_llm = bool(arguments.get("use_llm", True))
        horizon_days = int(arguments.get("horizon_days", 365))
        bundle = build_research_bundle(settings, ticker, horizon_days=horizon_days)
        return generate_report(bundle, use_llm=use_llm)
    if name == "compare.prices":
        symbols = arguments.get("symbols") or []
        if not isinstance(symbols, list) or not symbols:
            raise ValueError("symbols must be a non-empty list")
        start = arguments.get("start")
        end = arguments.get("end")
        horizon_days = int(arguments.get("horizon_days", 365))
        return compare_prices(settings, symbols, start=start, end=end, horizon_days=horizon_days)
    if name == "portfolio.stats":
        symbols = arguments.get("symbols") or []
        weights = arguments.get("weights") or []
        if not isinstance(symbols, list) or not isinstance(weights, list):
            raise ValueError("symbols and weights must be lists")
        start = arguments.get("start")
        end = arguments.get("end")
        horizon_days = int(arguments.get("horizon_days", 365))
        return portfolio_stats(
            settings,
            symbols=symbols,
            weights=weights,
            start=start,
            end=end,
            horizon_days=horizon_days,
        )
    extension = get_extension()
    if extension and hasattr(extension, "dispatch_tool"):
        return extension.dispatch_tool(settings, name, arguments)

    raise KeyError(f"Unhandled tool: {name}")
