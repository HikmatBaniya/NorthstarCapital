from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from .config import Settings
from .tools.company_tools import company_financials, company_profile, company_overview
from .tools.market_tools import market_history, market_quote
from .tools.news_tools import news_search
from .tools.sec_tools import sec_search
from .tools.sentiment_tools import sentiment_analyze
from .analytics import _returns_from_prices, _volatility, _max_drawdown_from_returns, _cagr_from_series


def _date_n_days_ago(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")


def build_research_bundle(
    settings: Settings,
    ticker: str,
    horizon_days: int = 365,
    news_limit: int = 6,
    filings_limit: int = 5,
) -> Dict[str, Any]:
    start = _date_n_days_ago(horizon_days)
    quote = market_quote(settings, ticker)
    history = market_history(settings, ticker, start=start, end=None, limit=1000)
    profile = company_profile(settings, ticker)
    financials = company_financials(settings, ticker)
    overview = company_overview(settings, ticker)
    filings = sec_search(settings, ticker, limit=filings_limit)
    news = news_search(settings, f"{ticker} earnings OR guidance OR revenue", news_limit)
    price_returns = _returns_from_prices(history.get("data", []))
    price_stats = {
        "cagr": _cagr_from_series(history.get("data", [])),
        "volatility": _volatility(price_returns),
        "max_drawdown": _max_drawdown_from_returns(price_returns),
    }
    sentiment = _news_sentiment(news)
    return {
        "ticker": ticker,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "quote": quote,
        "history": history,
        "profile": profile,
        "financials": financials,
        "overview": overview,
        "price_stats": price_stats,
        "filings": filings,
        "news": news,
        "news_sentiment": sentiment,
    }


def _news_sentiment(news: list[dict]) -> dict:
    if not news:
        return {"average_score": 0, "label": "neutral", "count": 0}
    scores = []
    for item in news:
        text = f"{item.get('title','')} {item.get('body','')}"
        result = sentiment_analyze(text)
        scores.append(result.get("score", 0))
    avg = sum(scores) / len(scores) if scores else 0
    label = "neutral"
    if avg > 0:
        label = "positive"
    elif avg < 0:
        label = "negative"
    return {"average_score": avg, "label": label, "count": len(scores)}
