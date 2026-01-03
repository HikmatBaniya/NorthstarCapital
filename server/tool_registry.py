from dataclasses import dataclass
from typing import Any, Dict, List

from .extensions import get_extension


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
]

_extension = get_extension()
if _extension and hasattr(_extension, "extra_tools"):
    try:
        TOOLS.extend(_extension.extra_tools())
    except Exception:
        pass
