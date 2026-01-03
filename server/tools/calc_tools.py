from __future__ import annotations

from typing import Any, Dict, List


def calc_returns(prices: List[float]) -> Dict[str, Any]:
    returns: List[float] = []
    for i in range(1, len(prices)):
        prev = prices[i - 1]
        curr = prices[i]
        if prev == 0:
            returns.append(0.0)
        else:
            returns.append((curr - prev) / prev)
    return {"returns": returns}


def calc_risk(returns: List[float]) -> Dict[str, Any]:
    if not returns:
        return {"volatility": 0.0, "mean": 0.0, "max_drawdown": 0.0}
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / max(len(returns) - 1, 1)
    volatility = variance ** 0.5
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
    return {"volatility": volatility, "mean": mean, "max_drawdown": max_dd}


def calc_portfolio(weights: List[float]) -> Dict[str, Any]:
    if not weights:
        return {"weights": [], "sum": 0.0}
    total = sum(weights)
    if total == 0:
        normalized = [0.0 for _ in weights]
    else:
        normalized = [w / total for w in weights]
    return {"weights": normalized, "sum": sum(normalized)}
