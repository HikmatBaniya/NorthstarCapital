# MCP Server and Tooling Documentation

This document explains how the MCP server and tools are structured and implemented in this project.

## MCP Server Overview
The MCP server is a FastAPI app that exposes tools over HTTP. It provides:
- A discovery endpoint that lists available tools and their input schemas.
- A single invoke endpoint that routes calls to the correct tool.

Server entrypoint:
- `server/main.py`

Endpoints:
- `GET /health`: status check.
- `GET /tools`: returns available tools with name, description, and input schema.
- `POST /invoke`: calls a tool by name with JSON arguments.

Invoke request format:
```
{
  "name": "tool.name",
  "arguments": { ... }
}
```

Invoke response format:
```
{
  "name": "tool.name",
  "result": { ... }
}
```

## Tool Discovery
Tools are defined in `server/tool_registry.py`. Each tool is a `ToolSpec` with:
- `name`: unique identifier (e.g., `market.quote`).
- `description`: short description for the LLM.
- `input_schema`: JSON schema describing tool arguments.

The `/tools` endpoint returns this registry as JSON for client discovery.

## Tool Dispatch
Tool dispatch is implemented in `server/main.py`:
- The server validates that the tool name exists in the registry.
- It validates required fields (e.g., `symbol`, `query`).
- It routes the call to the appropriate function in `server/tools/*`.
- It catches unexpected errors and returns HTTP 500.

## Tool Implementation Layout
Tool implementations live under `server/tools/` and are grouped by domain:
- `web_tools.py`: web search, fetch, and extract.
- `market_tools.py`: equities, FX, and crypto pricing.
- `macro_tools.py`: macro series via World Bank API.
- `news_tools.py`: finance news search (DuckDuckGo).
- `calc_tools.py`: basic analytics (returns, risk, portfolio).
- `sentiment_tools.py`: lightweight sentiment heuristic.

Each tool function accepts raw inputs and returns a JSON-serializable dict.

## Tool Behavior Details

### Web Tools
Files:
- `server/tools/web_tools.py`

Functions:
- `web_search(settings, query, max_results)`: DuckDuckGo search using `duckduckgo-search`.
- `web_fetch(settings, url, headers)`: HTTP GET and return HTML with optional headers.
- `web_fetch_browser(settings, url, headers)`: HTTP GET with browser-like headers.
- `web_extract(settings, html)`: strip scripts/styles and return visible text.

Notes:
- Uses `USER_AGENT` and `HTTP_TIMEOUT_SECONDS` from `.env`.
- Extraction is best-effort and returns a text truncation at 20k chars.

### Market Tools
Files:
- `server/tools/market_tools.py`

Functions:
- `market_quote`: Stooq quote (CSV endpoint).
- `market_history`: Stooq daily OHLCV (CSV endpoint).
- `market_fx`: open.er-api.com FX rates.
- `market_crypto`: CoinGecko price (simple/price endpoint).

Notes:
- Symbols are normalized for Stooq (`.us` appended for US equities).
- Crypto symbols are mapped to fixed CoinGecko IDs.

### Macro Tools
Files:
- `server/tools/macro_tools.py`

Functions:
- `macro_series`: World Bank series fetch using `INDICATOR:COUNTRY`.

Example:
- `NY.GDP.MKTP.CD:US`

### News Tools
Files:
- `server/tools/news_tools.py`

Functions:
- `news_search`: DuckDuckGo text search for finance news.

### Calculation Tools
Files:
- `server/tools/calc_tools.py`

Functions:
- `calc_returns`: computes simple returns from price list.
- `calc_risk`: computes mean, volatility, and max drawdown.
- `calc_portfolio`: normalizes weights to sum to 1.

### Sentiment Tools
Files:
- `server/tools/sentiment_tools.py`

Functions:
- `sentiment_analyze`: simple wordlist-based sentiment.

## Memory Tools (Database)
Files:
- `server/db.py`

Functions:
- `memory_put`: inserts content + tags into `memory_items` with optional `conversation_id`.
- `memory_search`: full-text search using `content_tsv`, optionally scoped by `conversation_id`.

Uses:
- SQLAlchemy engine created from `POSTGRES_DSN`.
- Full-text search (`plainto_tsquery`) for quick retrieval.

## Adding a New Tool
1) Add a `ToolSpec` to `server/tool_registry.py` with input schema.
2) Implement the tool in an appropriate `server/tools/*.py` file.
3) Import and route the tool in `server/main.py`.
4) Restart the server.

## Client Tool Consumption
The client discovers tools at runtime:
- `client/mcp_client.py` calls `/tools`.
- `client/llm_agent.py` builds LangChain tools dynamically from schemas.
- The LLM calls tools via the MCP server.

## Error Handling
Server-side:
- Missing inputs return HTTP 400.
- Unknown tools return HTTP 404.
- Unexpected errors return HTTP 500.

Client-side:
- UI surfaces exceptions in the chat window.
- Missing or invalid `GROQ_MODEL` returns Groq API errors.

## Relevant Files
- `server/main.py`
- `server/tool_registry.py`
- `server/tools/web_tools.py`
- `server/tools/market_tools.py`
- `server/tools/macro_tools.py`
- `server/tools/news_tools.py`
- `server/tools/calc_tools.py`
- `server/tools/sentiment_tools.py`
- `server/db.py`
- `client/mcp_client.py`
- `client/llm_agent.py`
