from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: Dict[str, Any]


TOOLS: List[ToolSpec] = [
    ToolSpec(
        name="web.search",
        description="General web search (DuckDuckGo).",
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    ),
    ToolSpec(
        name="web.fetch",
        description="Fetch HTML from a URL.",
        input_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}, "headers": {"type": "object"}},
            "required": ["url"],
        },
    ),
    ToolSpec(
        name="web.fetch_browser",
        description="Fetch HTML using browser-like headers.",
        input_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}, "headers": {"type": "object"}},
            "required": ["url"],
        },
    ),
    ToolSpec(
        name="web.extract",
        description="Extract main text from HTML.",
        input_schema={
            "type": "object",
            "properties": {"html": {"type": "string"}},
            "required": ["html"],
        },
    ),
    ToolSpec(
        name="market.quote",
        description="Fetch near-real-time quotes from free sources.",
        input_schema={
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"],
        },
    ),
    ToolSpec(
        name="market.history",
        description="Fetch historical OHLCV from free sources.",
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "start": {"type": "string"},
                "end": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["symbol"],
        },
    ),
    ToolSpec(
        name="market.fx",
        description="Fetch FX rates from free sources.",
        input_schema={
            "type": "object",
            "properties": {"pair": {"type": "string"}},
            "required": ["pair"],
        },
    ),
    ToolSpec(
        name="market.crypto",
        description="Fetch crypto prices from free sources.",
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "vs_currency": {"type": "string"},
            },
            "required": ["symbol"],
        },
    ),
    ToolSpec(
        name="company.profile",
        description="Company metadata and profile (SEC).",
        input_schema={
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    ),
    ToolSpec(
        name="company.financials",
        description="Key financial statements and metrics (SEC XBRL).",
        input_schema={
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    ),
    ToolSpec(
        name="sec.search",
        description="Search SEC filings by ticker or CIK.",
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"],
        },
    ),
    ToolSpec(
        name="sec.filing",
        description="Fetch and extract SEC filing content.",
        input_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    ),
    ToolSpec(
        name="macro.series",
        description="Fetch macro series from World Bank (use INDICATOR:COUNTRY).",
        input_schema={
            "type": "object",
            "properties": {"series_id": {"type": "string"}},
            "required": ["series_id"],
        },
    ),
    ToolSpec(
        name="news.search",
        description="Search finance news.",
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}},
            "required": ["query"],
        },
    ),
    ToolSpec(
        name="news.extract",
        description="Extract article text from a URL.",
        input_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    ),
    ToolSpec(
        name="nepse.company_details",
        description="Fetch NEPSE company details by symbol.",
        input_schema={
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"],
        },
    ),
    ToolSpec(
        name="nepse.price_volume",
        description="Fetch NEPSE price/volume list.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.live_market",
        description="Fetch NEPSE live market data.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.symbol_snapshot",
        description="Fetch compact NEPSE snapshot for a symbol.",
        input_schema={
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"],
        },
    ),
    ToolSpec(
        name="nepse.summary",
        description="Fetch NEPSE market summary.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.index",
        description="Fetch NEPSE main index data.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.subindices",
        description="Fetch NEPSE sub-index data.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.is_open",
        description="Fetch NEPSE market open status.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.top_gainers",
        description="Fetch NEPSE top gainers.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.top_losers",
        description="Fetch NEPSE top losers.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.top_trade_scrips",
        description="Fetch NEPSE top trade scrips.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.top_transaction_scrips",
        description="Fetch NEPSE top transaction scrips.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.top_turnover_scrips",
        description="Fetch NEPSE top turnover scrips.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.supply_demand",
        description="Fetch NEPSE supply/demand lists.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.trade_turnover_transaction",
        description="Fetch NEPSE trade/turnover/transaction subindex breakdown.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.company_list",
        description="Fetch NEPSE company list.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.sector_scrips",
        description="Fetch NEPSE sector scrips list.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.security_list",
        description="Fetch NEPSE security list.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.price_volume_history",
        description="Fetch NEPSE price volume history by symbol.",
        input_schema={
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"],
        },
    ),
    ToolSpec(
        name="nepse.floorsheet",
        description="Fetch NEPSE floorsheet.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="nepse.floorsheet_of",
        description="Fetch NEPSE floorsheet by symbol.",
        input_schema={
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"],
        },
    ),
    ToolSpec(
        name="nepse.daily_scrip_price_graph",
        description="Fetch NEPSE daily scrip price graph by symbol.",
        input_schema={
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"],
        },
    ),
    ToolSpec(
        name="nepse.daily_index_graph",
        description="Fetch NEPSE daily index graph by kind (nepse, sensitive, float, bank, etc).",
        input_schema={
            "type": "object",
            "properties": {"kind": {"type": "string"}},
            "required": ["kind"],
        },
    ),
    ToolSpec(
        name="sentiment.analyze",
        description="Simple sentiment scoring.",
        input_schema={
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    ),
    ToolSpec(
        name="calc.returns",
        description="Calculate returns for a price series.",
        input_schema={
            "type": "object",
            "properties": {"prices": {"type": "array"}},
            "required": ["prices"],
        },
    ),
    ToolSpec(
        name="calc.risk",
        description="Calculate volatility, drawdown, beta.",
        input_schema={
            "type": "object",
            "properties": {"returns": {"type": "array"}},
            "required": ["returns"],
        },
    ),
    ToolSpec(
        name="calc.portfolio",
        description="Compute portfolio stats.",
        input_schema={
            "type": "object",
            "properties": {"weights": {"type": "array"}},
            "required": ["weights"],
        },
    ),
    ToolSpec(
        name="memory.put",
        description="Store memory item.",
        input_schema={
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "tags": {"type": "array"},
                "conversation_id": {"type": "string"},
            },
            "required": ["content"],
        },
    ),
    ToolSpec(
        name="memory.search",
        description="Semantic search over memory.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
                "conversation_id": {"type": "string"},
            },
            "required": ["query"],
        },
    ),
    ToolSpec(
        name="research.bundle",
        description="Build a comprehensive research bundle for a ticker.",
        input_schema={
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "horizon_days": {"type": "integer"},
                "news_limit": {"type": "integer"},
                "filings_limit": {"type": "integer"},
            },
            "required": ["ticker"],
        },
    ),
    ToolSpec(
        name="report.generate",
        description="Generate report HTML and Markdown from a research bundle.",
        input_schema={
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "use_llm": {"type": "boolean"},
                "horizon_days": {"type": "integer"},
            },
            "required": ["ticker"],
        },
    ),
    ToolSpec(
        name="compare.prices",
        description="Compare price performance across tickers.",
        input_schema={
            "type": "object",
            "properties": {
                "symbols": {"type": "array"},
                "start": {"type": "string"},
                "end": {"type": "string"},
                "horizon_days": {"type": "integer"},
            },
            "required": ["symbols"],
        },
    ),
    ToolSpec(
        name="portfolio.stats",
        description="Basic portfolio risk/return stats.",
        input_schema={
            "type": "object",
            "properties": {
                "symbols": {"type": "array"},
                "weights": {"type": "array"},
                "start": {"type": "string"},
                "end": {"type": "string"},
                "horizon_days": {"type": "integer"},
            },
            "required": ["symbols", "weights"],
        },
    ),
    ToolSpec(
        name="paper.portfolios",
        description="List paper trading portfolios.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="paper.portfolio_create",
        description="Create a paper trading portfolio.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "starting_cash": {"type": "number"},
                "currency": {"type": "string"},
            },
        },
    ),
    ToolSpec(
        name="paper.portfolio_summary",
        description="Get paper portfolio summary including cash and positions.",
        input_schema={
            "type": "object",
            "properties": {"portfolio_id": {"type": "string"}},
            "required": ["portfolio_id"],
        },
    ),
    ToolSpec(
        name="paper.positions",
        description="List paper portfolio positions.",
        input_schema={
            "type": "object",
            "properties": {"portfolio_id": {"type": "string"}},
            "required": ["portfolio_id"],
        },
    ),
    ToolSpec(
        name="paper.trades",
        description="List paper portfolio trades.",
        input_schema={
            "type": "object",
            "properties": {"portfolio_id": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["portfolio_id"],
        },
    ),
    ToolSpec(
        name="paper.trade_proposals",
        description="List paper trade proposals.",
        input_schema={
            "type": "object",
            "properties": {"portfolio_id": {"type": "string"}, "status": {"type": "string"}},
            "required": ["portfolio_id"],
        },
    ),
    ToolSpec(
        name="paper.trade_propose",
        description="Propose a paper trade (requires approval).",
        input_schema={
            "type": "object",
            "properties": {
                "portfolio_id": {"type": "string"},
                "symbol": {"type": "string"},
                "side": {"type": "string"},
                "quantity": {"type": "number"},
                "reason": {"type": "string"},
                "model": {"type": "string"},
            },
            "required": ["portfolio_id", "symbol", "side", "quantity"],
        },
    ),
]
