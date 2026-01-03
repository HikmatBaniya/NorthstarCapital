# MCP Tool Catalog (Planned)

## Web and Search
- web.search: general web search (DuckDuckGo)
- web.fetch: fetch HTML (with user agent and timeout)
- web.fetch_browser: fetch HTML using browser-like headers
- web.extract: extract main text from HTML

## Market Data (Free)
- market.quote: real-time-ish quotes (free public sources)
- market.history: historical OHLCV via free endpoints
- market.fx: FX rates
- market.crypto: crypto prices

## Macro and Econ
- macro.series: World Bank series fetch (use INDICATOR:COUNTRY)

## Fundamentals and Filings
- company.profile: company metadata (SEC)
- company.financials: key financial statements (SEC XBRL)
- sec.search: SEC filings search
- sec.filing: SEC filing fetch and extract

## News and Sentiment
- news.search: finance news search (DuckDuckGo)
- news.extract: article extract
- sentiment.analyze: simple sentiment scoring

## Analytics and Utilities
- calc.returns: return calculations
- calc.risk: volatility, beta, drawdown
- calc.portfolio: basic portfolio stats
- format.table: render tabular results

## Memory
- memory.put: store conversation facts and notes
- memory.search: full-text search over stored memory

## Research and Reports
- research.bundle: comprehensive research bundle for a ticker
- report.generate: report generation (HTML + Markdown)
- compare.prices: price performance comparison
- portfolio.stats: basic portfolio analytics
