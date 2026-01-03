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
from .tools.nepse_tools import (
    nepse_company_details,
    nepse_price_volume,
    nepse_live_market,
    nepse_symbol_snapshot,
    nepse_summary,
    nepse_index,
    nepse_subindices,
    nepse_is_open,
    nepse_top_gainers,
    nepse_top_losers,
    nepse_top_trade_scrips,
    nepse_top_transaction_scrips,
    nepse_top_turnover_scrips,
    nepse_supply_demand,
    nepse_trade_turnover_transaction,
    nepse_company_list,
    nepse_sector_scrips,
    nepse_security_list,
    nepse_price_volume_history,
    nepse_floorsheet,
    nepse_floorsheet_of,
    nepse_daily_scrip_price_graph,
    nepse_daily_index_graph,
)
from .tools.sec_tools import sec_filing, sec_search
from .tools.sentiment_tools import sentiment_analyze
from .research import build_research_bundle
from .reporting import generate_report
from .analytics import compare_prices, portfolio_stats
from .tools.web_tools import web_extract, web_fetch, web_fetch_browser, web_search
from .tools.paper_tools import (
    paper_list_portfolios,
    paper_portfolio_summary,
    paper_positions,
    paper_trades,
    paper_trade_proposals,
    paper_trade_propose,
    paper_create_portfolio,
)


def dispatch_tool(settings: Settings, name: str, arguments: Dict[str, Any]) -> Any:
    def _truncate_list(items: List[Any], limit: int) -> List[Any]:
        if len(items) <= limit:
            return items
        return items[:limit]

    def _truncate_sector_map(data: Dict[str, Any], limit: int) -> Dict[str, Any]:
        truncated: Dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, list):
                truncated[key] = _truncate_list(value, limit)
            else:
                truncated[key] = value
        truncated["_truncated"] = True
        truncated["_limit"] = limit
        return truncated
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
    if name == "nepse.company_details":
        symbol = str(arguments.get("symbol", "")).strip()
        if not symbol:
            raise ValueError("symbol is required")
        return nepse_company_details(settings, symbol)
    if name == "nepse.price_volume":
        data = nepse_price_volume(settings)
        return {"items": _truncate_list(data, 200), "_truncated": len(data) > 200, "_limit": 200}
    if name == "nepse.live_market":
        data = nepse_live_market(settings)
        return {"items": _truncate_list(data, 200), "_truncated": len(data) > 200, "_limit": 200}
    if name == "nepse.symbol_snapshot":
        symbol = str(arguments.get("symbol", "")).strip()
        if not symbol:
            raise ValueError("symbol is required")
        return nepse_symbol_snapshot(settings, symbol)
    if name == "nepse.summary":
        return nepse_summary(settings)
    if name == "nepse.index":
        return nepse_index(settings)
    if name == "nepse.subindices":
        return nepse_subindices(settings)
    if name == "nepse.is_open":
        return nepse_is_open(settings)
    if name == "nepse.top_gainers":
        return nepse_top_gainers(settings)
    if name == "nepse.top_losers":
        return nepse_top_losers(settings)
    if name == "nepse.top_trade_scrips":
        return nepse_top_trade_scrips(settings)
    if name == "nepse.top_transaction_scrips":
        return nepse_top_transaction_scrips(settings)
    if name == "nepse.top_turnover_scrips":
        return nepse_top_turnover_scrips(settings)
    if name == "nepse.supply_demand":
        return nepse_supply_demand(settings)
    if name == "nepse.trade_turnover_transaction":
        return nepse_trade_turnover_transaction(settings)
    if name == "nepse.company_list":
        data = nepse_company_list(settings)
        return {"items": _truncate_list(data, 200), "_truncated": len(data) > 200, "_limit": 200}
    if name == "nepse.sector_scrips":
        data = nepse_sector_scrips(settings)
        return _truncate_sector_map(data, 50)
    if name == "nepse.security_list":
        data = nepse_security_list(settings)
        return {"items": _truncate_list(data, 200), "_truncated": len(data) > 200, "_limit": 200}
    if name == "nepse.price_volume_history":
        symbol = str(arguments.get("symbol", "")).strip()
        if not symbol:
            raise ValueError("symbol is required")
        data = nepse_price_volume_history(settings, symbol)
        return {"items": _truncate_list(data, 200), "_truncated": len(data) > 200, "_limit": 200}
    if name == "nepse.floorsheet":
        data = nepse_floorsheet(settings)
        return {"items": _truncate_list(data, 200), "_truncated": len(data) > 200, "_limit": 200}
    if name == "nepse.floorsheet_of":
        symbol = str(arguments.get("symbol", "")).strip()
        if not symbol:
            raise ValueError("symbol is required")
        data = nepse_floorsheet_of(settings, symbol)
        return {"items": _truncate_list(data, 200), "_truncated": len(data) > 200, "_limit": 200}
    if name == "nepse.daily_scrip_price_graph":
        symbol = str(arguments.get("symbol", "")).strip()
        if not symbol:
            raise ValueError("symbol is required")
        return nepse_daily_scrip_price_graph(settings, symbol)
    if name == "nepse.daily_index_graph":
        kind = str(arguments.get("kind", "")).strip()
        if not kind:
            raise ValueError("kind is required")
        return nepse_daily_index_graph(settings, kind)
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
    if name == "paper.portfolios":
        return paper_list_portfolios(settings)
    if name == "paper.portfolio_create":
        name = arguments.get("name")
        starting_cash = float(arguments.get("starting_cash", 100000.0))
        currency = str(arguments.get("currency", "NPR")).strip() or "NPR"
        return paper_create_portfolio(settings, name=name, starting_cash=starting_cash, currency=currency)
    if name == "paper.portfolio_summary":
        portfolio_id = str(arguments.get("portfolio_id", "")).strip()
        if not portfolio_id:
            raise ValueError("portfolio_id is required")
        return paper_portfolio_summary(settings, portfolio_id)
    if name == "paper.positions":
        portfolio_id = str(arguments.get("portfolio_id", "")).strip()
        if not portfolio_id:
            raise ValueError("portfolio_id is required")
        return paper_positions(settings, portfolio_id)
    if name == "paper.trades":
        portfolio_id = str(arguments.get("portfolio_id", "")).strip()
        if not portfolio_id:
            raise ValueError("portfolio_id is required")
        limit = int(arguments.get("limit", 200))
        return paper_trades(settings, portfolio_id, limit=limit)
    if name == "paper.trade_proposals":
        portfolio_id = str(arguments.get("portfolio_id", "")).strip()
        if not portfolio_id:
            raise ValueError("portfolio_id is required")
        status = arguments.get("status")
        return paper_trade_proposals(settings, portfolio_id, status=status)
    if name == "paper.trade_propose":
        portfolio_id = str(arguments.get("portfolio_id", "")).strip()
        symbol = str(arguments.get("symbol", "")).strip()
        side = str(arguments.get("side", "")).strip().lower()
        quantity = float(arguments.get("quantity", 0))
        if not portfolio_id:
            raise ValueError("portfolio_id is required")
        if not symbol:
            raise ValueError("symbol is required")
        if side not in ("buy", "sell"):
            raise ValueError("side must be buy or sell")
        if quantity <= 0:
            raise ValueError("quantity must be > 0")
        reason = arguments.get("reason")
        model = arguments.get("model")
        return paper_trade_propose(
            settings,
            portfolio_id=portfolio_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            reason=reason,
            model=model,
        )

    raise KeyError(f"Unhandled tool: {name}")
