# Financial LLM Agent Documentation

This document describes the architecture, configuration, tools, data sources, database, and usage of the Financial LLM Agent application.

## Overview
The application consists of:
- An MCP-style HTTP server that exposes finance-related tools.
- A Tkinter desktop client that uses a Groq-backed LLM to call tools and answer questions.
- A PostgreSQL database for memory and chat storage (full-text search, no vector extension).

Core capabilities:
- Web search, fetch, and text extraction.
- Market quotes and historical OHLCV (Stooq).
- FX rates (open.er-api.com).
- Crypto prices (CoinGecko).
- Macro series (World Bank).
- News search (DuckDuckGo).
- Calculations (returns, risk, portfolio).
- Simple sentiment analysis.
- Memory storage and search (Postgres FTS).

## Repository Structure
- `server/`: MCP HTTP server and tool implementations.
- `client/`: Tkinter UI and LLM orchestration.
- `shared/`: tool catalog and shared docs.
- `data/`: reserved for datasets (empty by default).
- `scripts/`: reserved for helper scripts.
- `tests/`: reserved for tests.
- `requirements.txt`: Python dependencies.
- `.env`: runtime configuration (not checked in).
- `.env.example`: example env file.
- `DOCUMENTATION.md`: this file.

## Requirements
- Python 3.11.7
- PostgreSQL 15+ recommended (works with 17)
- Internet access for public APIs
- Groq API key (LLM inference)

## Configuration
Create a `.env` file in the project root using `.env.example` as a template.

Required values:
- `GROQ_API_KEY`: Groq API key.
- `POSTGRES_DSN`: SQLAlchemy DSN for PostgreSQL.
- `MCP_SERVER_URL`: MCP server URL for the client.

Optional values:
- `GROQ_MODEL`: LLM model ID (see Groq model list).
- `USER_AGENT`: HTTP User-Agent for web requests.
- `HTTP_TIMEOUT_SECONDS`: request timeout in seconds.
- `HTTP_RETRY_COUNT`: retry attempts for transient HTTP errors.
- `HTTP_RETRY_BACKOFF_SECONDS`: base backoff seconds between retries.
- `WEB_SEARCH_PROVIDER`: currently only `duckduckgo`.

Example `.env`:
```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
POSTGRES_DSN=postgresql+psycopg2://postgres:postgres@localhost:5432/financellm
MCP_SERVER_URL=http://127.0.0.1:8000
USER_AGENT=FinancialLLM/1.0
HTTP_TIMEOUT_SECONDS=30
HTTP_RETRY_COUNT=3
HTTP_RETRY_BACKOFF_SECONDS=0.4
WEB_SEARCH_PROVIDER=duckduckgo
```

## Database
This app uses PostgreSQL with full-text search (no `vector` extension).

Schema (run once):
```
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS memory_items (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    tags TEXT[] NOT NULL DEFAULT '{}',
    conversation_id UUID,
    content_tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
    ON messages(conversation_id);

CREATE INDEX IF NOT EXISTS idx_memory_items_tags
    ON memory_items USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_memory_items_tsv
    ON memory_items USING GIN(content_tsv);

CREATE INDEX IF NOT EXISTS idx_memory_items_conversation
    ON memory_items(conversation_id);
```

Additional schema for company research + workspace:
```
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    sector TEXT,
    industry TEXT,
    country TEXT,
    website TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS company_identifiers (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    id_type TEXT NOT NULL,
    id_value TEXT NOT NULL,
    source TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (id_type, id_value)
);

CREATE TABLE IF NOT EXISTS company_profiles (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL UNIQUE REFERENCES companies(id) ON DELETE CASCADE,
    profile JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS company_people (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    role TEXT,
    start_date DATE,
    end_date DATE,
    bio TEXT,
    source TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS company_images (
    id UUID PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    image_url TEXT NOT NULL,
    local_path TEXT,
    license TEXT,
    attribution TEXT,
    source TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_company_images_entity
    ON company_images(entity_type, entity_id);

CREATE TABLE IF NOT EXISTS company_documents (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    doc_type TEXT,
    title TEXT,
    url TEXT,
    content TEXT,
    source TEXT,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS company_workspaces (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL UNIQUE REFERENCES companies(id) ON DELETE CASCADE,
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shelves (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shelf_items (
    id UUID PRIMARY KEY,
    shelf_id UUID NOT NULL REFERENCES shelves(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (shelf_id, company_id)
);

CREATE TABLE IF NOT EXISTS company_financials (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    metric TEXT NOT NULL,
    value DOUBLE PRECISION,
    period_start DATE,
    period_end DATE,
    unit TEXT,
    currency TEXT,
    source TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_company_financials_company
    ON company_financials(company_id);

CREATE INDEX IF NOT EXISTS idx_company_financials_metric
    ON company_financials(metric);

CREATE TABLE IF NOT EXISTS company_subsidiaries (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    country TEXT,
    ownership_pct DOUBLE PRECISION,
    source TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_company_subsidiaries_company
    ON company_subsidiaries(company_id);

CREATE TABLE IF NOT EXISTS company_ownership (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    holder_name TEXT NOT NULL,
    holder_type TEXT,
    percent DOUBLE PRECISION,
    shares DOUBLE PRECISION,
    as_of_date DATE,
    source TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_company_ownership_company
    ON company_ownership(company_id);

CREATE INDEX IF NOT EXISTS idx_company_ownership_holder
    ON company_ownership(holder_name);
```

Notes:
- `conversations` and `messages` are reserved for future conversation storage.
- `memory_items` stores user/assistant memory with tags and full-text search.

## Installation
1) Create and activate a virtual environment.
2) Install dependencies:
   `python -m pip install -r requirements.txt`
3) Ensure `.env` is configured.

## Running
Start the MCP server:
`python -m server.main`

Start the UI client:
`python -m client.app`

## MCP Server
The server is a FastAPI app with the following endpoints:
- `GET /health`: returns status.
- `GET /tools`: lists available tools with input schema.
- `POST /invoke`: invokes a tool.

Invoke payload:
```
{
  "name": "tool.name",
  "arguments": { ... }
}
```

Invoke response:
```
{
  "name": "tool.name",
  "result": { ... }
}
```

## Tool Catalog
Tools are defined in `server/tool_registry.py` and implemented in `server/tools/`.

### Web and Search
- `web.search`: DuckDuckGo search.
  - Input: `query`
- `web.fetch`: HTTP GET to a URL.
  - Input: `url`, optional `headers`
- `web.fetch_browser`: HTTP GET with browser-like headers.
  - Input: `url`, optional `headers`
- `web.extract`: HTML to text (basic extraction).
  - Input: `html`

### Market Data (Free)
- `market.quote`: Stooq quote.
  - Input: `symbol`
- `market.history`: Stooq daily history.
  - Input: `symbol`, optional `start`, `end`, `limit`
- `market.fx`: FX rates via open.er-api.com.
  - Input: `pair` (e.g., `USD/EUR`)
- `market.crypto`: CoinGecko price.
  - Input: `symbol` (BTC, ETH, SOL, ADA, XRP, DOGE, USDT, BNB), optional `vs_currency`

### Macro and Econ
- `macro.series`: World Bank series.
  - Input: `series_id` formatted as `INDICATOR:COUNTRY`
  - Example: `NY.GDP.MKTP.CD:US`

### News and Sentiment
- `news.search`: DuckDuckGo search (finance news).
  - Input: `query`, optional `max_results`
- `news.extract`: fetch + extract article text.
  - Input: `url`
- `sentiment.analyze`: simple token-based sentiment.
  - Input: `text`

### Analytics and Utilities
- `calc.returns`: returns series from prices.
  - Input: `prices`
- `calc.risk`: volatility, mean, drawdown.
  - Input: `returns`
- `calc.portfolio`: normalize weights.
  - Input: `weights`

### Memory
- `memory.put`: insert a memory item.
  - Input: `content`, optional `tags`, `conversation_id`
- `memory.search`: full-text search on memory.
  - Input: `query`, optional `limit`, `conversation_id`

## Data Sources
Default free data sources used:
- Stooq: quotes and historical OHLCV.
- open.er-api.com: FX rates.
- CoinGecko: crypto spot prices.
- World Bank API: macro series.
- DuckDuckGo: web and news search.

These sources can be replaced or extended by adding new tools.

## Client (Tkinter UI)
The UI:
- Presents a chat window with a futuristic theme.
- Allows toggling memory usage and memory storage.
- Sends user messages to the LLM and displays responses.

Key behaviors:
- On each query, optional memory context is appended to the prompt.
- The LLM can call MCP tools via LangChain tool calling.
- If "Store to memory" is enabled, user and assistant messages are stored.

## LLM Orchestration
The client uses:
- `langchain` + `langchain_groq`
- Tool discovery from the MCP server (`/tools`)
- Automatic tool invocation via LangChain's tool calling agent

Prompting:
- System prompt is defined in `client/llm_agent.py` (`SYSTEM_PROMPT`).
- Tool outputs are used to produce grounded responses.

## Known Limitations
- DuckDuckGo may rate-limit; add retries if needed.
- Stooq symbols often require `.us` for US equities; auto-normalized.
- CoinGecko symbols are mapped by a small static map.
- No caching or rate limiting yet (planned).
- `conversations` and `messages` are not yet wired into the client.

## Troubleshooting
Common issues:
- Model decommissioned: update `GROQ_MODEL` to an active model.
- MCP server unreachable: check `MCP_SERVER_URL` and server logs.
- Database errors: verify `POSTGRES_DSN` and schema.
- Memory search returns empty: ensure `memory.put` was called.

## Security Notes
- Do not expose the MCP server to the public internet without auth.
- Store `.env` securely; it contains API keys.
- Web extraction is best-effort and may include noise.

## Extending the App
Suggested next steps:
- Add SEC filings tools.
- Add caching and rate limiting.
- Add portfolio analytics with external data.
- Add user accounts and conversation persistence.

## File Reference Guide
- Server entrypoint: `server/main.py`
- MCP tools registry: `server/tool_registry.py`
- Web tools: `server/tools/web_tools.py`
- Market tools: `server/tools/market_tools.py`
- Macro tools: `server/tools/macro_tools.py`
- News tools: `server/tools/news_tools.py`
- Calc tools: `server/tools/calc_tools.py`
- Sentiment tools: `server/tools/sentiment_tools.py`
- DB helpers: `server/db.py`
- LLM client: `client/llm_agent.py`
- Tkinter UI: `client/app.py`
