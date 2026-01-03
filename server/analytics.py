from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .tools.market_tools import market_history
from .tools.calc_tools import calc_risk
from .config import Settings


def _date_n_days_ago(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")


def compare_prices(
    settings: Settings,
    symbols: List[str],
    start: Optional[str] = None,
    end: Optional[str] = None,
    horizon_days: int = 365,
) -> Dict[str, Any]:
    if not start and not end:
        start = _date_n_days_ago(horizon_days)
    series: Dict[str, List[Dict[str, Any]]] = {}
    performance: Dict[str, float] = {}
    normalized: Dict[str, List[Dict[str, Any]]] = {}
    volatility: Dict[str, float] = {}
    drawdown: Dict[str, float] = {}
    cagr: Dict[str, float] = {}
    for symbol in symbols:
        hist = market_history(settings, symbol, start, end, limit=2000)
        data = hist.get("data", [])
        if not data:
            series[symbol] = []
            performance[symbol] = 0.0
            normalized[symbol] = []
            volatility[symbol] = 0.0
            drawdown[symbol] = 0.0
            cagr[symbol] = 0.0
            continue
        series[symbol] = data
        start_close = data[0].get("close", 0) or 0
        end_close = data[-1].get("close", 0) or 0
        if start_close:
            performance[symbol] = (end_close - start_close) / start_close
        else:
            performance[symbol] = 0.0
        normalized[symbol] = _normalize_series(data)
        returns = _returns_from_prices(data)
        volatility[symbol] = _volatility(returns)
        drawdown[symbol] = _max_drawdown_from_returns(returns)
        cagr[symbol] = _cagr_from_series(data)
    return {
        "start": start,
        "end": end,
        "performance": performance,
        "series": series,
        "normalized": normalized,
        "volatility": volatility,
        "max_drawdown": drawdown,
        "cagr": cagr,
        "correlation": _correlation_matrix(series),
        "summary": _compare_summary(performance),
    }


def portfolio_stats(
    settings: Settings,
    symbols: List[str],
    weights: List[float],
    start: Optional[str] = None,
    end: Optional[str] = None,
    horizon_days: int = 365,
) -> Dict[str, Any]:
    if not symbols or not weights or len(symbols) != len(weights):
        return {"error": "symbols and weights must be same length"}
    if not start and not end:
        start = _date_n_days_ago(horizon_days)

    histories: Dict[str, Dict[str, float]] = {}
    for symbol in symbols:
        hist = market_history(settings, symbol, start, end, limit=2000)
        price_map = {row["date"]: row.get("close", 0) for row in hist.get("data", [])}
        histories[symbol] = price_map

    common_dates = set.intersection(*(set(v.keys()) for v in histories.values()))
    dates = sorted(common_dates)
    if len(dates) < 2:
        return {"error": "not_enough_data"}

    returns: List[float] = []
    for i in range(1, len(dates)):
        prev_date = dates[i - 1]
        curr_date = dates[i]
        portfolio_prev = 0.0
        portfolio_curr = 0.0
        for symbol, weight in zip(symbols, weights):
            portfolio_prev += weight * histories[symbol].get(prev_date, 0)
            portfolio_curr += weight * histories[symbol].get(curr_date, 0)
        if portfolio_prev == 0:
            returns.append(0.0)
        else:
            returns.append((portfolio_curr - portfolio_prev) / portfolio_prev)

    risk = calc_risk(returns)
    sharpe = _ratio(risk["mean"], risk["volatility"])
    sortino = _sortino(returns, risk["mean"])
    cumulative_return = _cumulative_return(returns)
    return {
        "start": start,
        "end": end,
        "symbols": symbols,
        "weights": weights,
        "return_series": returns,
        "risk": risk,
        "sharpe": sharpe,
        "sortino": sortino,
        "cumulative_return": cumulative_return,
    }


def _returns_from_prices(data: List[Dict[str, Any]]) -> List[float]:
    returns: List[float] = []
    for i in range(1, len(data)):
        prev = data[i - 1].get("close", 0) or 0
        curr = data[i].get("close", 0) or 0
        if prev == 0:
            returns.append(0.0)
        else:
            returns.append((curr - prev) / prev)
    return returns


def _volatility(returns: List[float]) -> float:
    if not returns:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / max(len(returns) - 1, 1)
    return variance ** 0.5


def _cumulative_return(returns: List[float]) -> float:
    cumulative = 1.0
    for r in returns:
        cumulative *= 1 + r
    return cumulative - 1


def _max_drawdown_from_returns(returns: List[float]) -> float:
    cumulative = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cumulative *= 1 + r
        if cumulative > peak:
            peak = cumulative
        drawdown = (peak - cumulative) / peak
        if drawdown > max_dd:
            max_dd = drawdown
    return max_dd


def _normalize_series(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not data:
        return []
    base = data[0].get("close", 0) or 0
    if base == 0:
        return [{"date": row.get("date"), "value": 0.0} for row in data]
    return [
        {"date": row.get("date"), "value": (row.get("close", 0) or 0) / base}
        for row in data
    ]


def _cagr_from_series(data: List[Dict[str, Any]]) -> float:
    if len(data) < 2:
        return 0.0
    start_price = data[0].get("close", 0) or 0
    end_price = data[-1].get("close", 0) or 0
    if start_price == 0:
        return 0.0
    try:
        start_date = datetime.strptime(data[0].get("date"), "%Y-%m-%d")
        end_date = datetime.strptime(data[-1].get("date"), "%Y-%m-%d")
        days = max((end_date - start_date).days, 1)
    except Exception:
        days = 365
    years = days / 365.0
    return (end_price / start_price) ** (1 / years) - 1


def _ratio(mean: float, vol: float) -> float:
    if not vol:
        return 0.0
    return mean / vol


def _sortino(returns: List[float], mean: float) -> float:
    downside = [r for r in returns if r < 0]
    if not downside:
        return 0.0
    downside_vol = _volatility(downside)
    if downside_vol == 0:
        return 0.0
    return mean / downside_vol


def _correlation_matrix(series: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, float]]:
    symbols = list(series.keys())
    price_maps = {
        sym: {row["date"]: row.get("close", 0) for row in series[sym] if row.get("date")}
        for sym in symbols
    }
    common_dates = set.intersection(*(set(v.keys()) for v in price_maps.values())) if symbols else set()
    dates = sorted(common_dates)
    returns_map: Dict[str, List[float]] = {}
    for sym in symbols:
        prices = [price_maps[sym][d] for d in dates]
        returns_map[sym] = _returns_from_prices([{"close": p} for p in prices])
    corr: Dict[str, Dict[str, float]] = {}
    for s1 in symbols:
        corr[s1] = {}
        for s2 in symbols:
            corr[s1][s2] = _correlation(returns_map.get(s1, []), returns_map.get(s2, []))
    return corr


def _correlation(xs: List[float], ys: List[float]) -> float:
    n = min(len(xs), len(ys))
    if n < 2:
        return 0.0
    xs = xs[:n]
    ys = ys[:n]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / (n - 1)
    std_x = _volatility(xs)
    std_y = _volatility(ys)
    if std_x == 0 or std_y == 0:
        return 0.0
    return cov / (std_x * std_y)


def _compare_summary(performance: Dict[str, float]) -> Dict[str, Any]:
    if not performance:
        return {}
    sorted_items = sorted(performance.items(), key=lambda x: x[1], reverse=True)
    best = sorted_items[0]
    worst = sorted_items[-1]
    return {
        "best": {"symbol": best[0], "return": best[1]},
        "worst": {"symbol": worst[0], "return": worst[1]},
    }
