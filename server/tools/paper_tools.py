from __future__ import annotations

from typing import Any, Dict, List

from .nepse_tools import nepse_live_market, nepse_price_volume
from ..config import Settings
from ..db import (
    create_paper_portfolio,
    get_paper_portfolio,
    list_paper_portfolios,
    list_paper_positions,
    list_paper_trades,
    list_paper_trade_proposals,
    add_paper_cash_ledger,
    create_paper_trade_proposal,
    approve_paper_trade_proposal,
    reject_paper_trade_proposal,
    get_paper_cash_balance,
)


def _symbol_price(settings: Settings, symbol: str) -> float | None:
    symbol_upper = symbol.upper()
    live = nepse_live_market(settings)
    for row in live:
        if row.get("symbol") == symbol_upper:
            price = row.get("lastTradedPrice")
            return float(price) if price is not None else None
    prices = nepse_price_volume(settings)
    for row in prices:
        if row.get("symbol") == symbol_upper:
            price = row.get("lastTradedPrice")
            return float(price) if price is not None else None
    return None


def paper_create_portfolio(
    settings: Settings, name: str | None = None, starting_cash: float = 100000.0, currency: str = "NPR"
) -> Dict[str, Any]:
    return create_paper_portfolio(name=name, starting_cash=starting_cash, currency=currency)


def paper_list_portfolios(settings: Settings) -> List[Dict[str, Any]]:
    return list_paper_portfolios()


def paper_portfolio_summary(settings: Settings, portfolio_id: str) -> Dict[str, Any]:
    portfolio = get_paper_portfolio(portfolio_id)
    if not portfolio:
        return {}
    positions = list_paper_positions(portfolio_id)
    cash = get_paper_cash_balance(portfolio_id)
    market_value = 0.0
    enriched_positions = []
    for pos in positions:
        symbol = pos.get("symbol")
        price = _symbol_price(settings, symbol)
        qty = float(pos.get("quantity") or 0)
        avg_cost = float(pos.get("avg_cost") or 0)
        value = (price if price is not None else avg_cost) * qty
        market_value += value
        enriched_positions.append(
            {
                **pos,
                "last_price": price,
                "market_value": value,
                "unrealized_pnl": None if price is None else (price - avg_cost) * qty,
            }
        )
    total_value = cash + market_value
    return {
        "portfolio": portfolio,
        "cash": cash,
        "positions": enriched_positions,
        "market_value": market_value,
        "total_value": total_value,
    }


def paper_positions(settings: Settings, portfolio_id: str) -> List[Dict[str, Any]]:
    return list_paper_positions(portfolio_id)


def paper_trades(settings: Settings, portfolio_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    return list_paper_trades(portfolio_id, limit=limit)


def paper_trade_proposals(
    settings: Settings, portfolio_id: str, status: str | None = None
) -> List[Dict[str, Any]]:
    return list_paper_trade_proposals(portfolio_id, status=status)


def paper_add_cash(settings: Settings, portfolio_id: str, amount: float, reason: str | None = None) -> Dict[str, Any]:
    return add_paper_cash_ledger(portfolio_id, amount, reason)


def paper_trade_propose(
    settings: Settings,
    portfolio_id: str,
    symbol: str,
    side: str,
    quantity: float,
    reason: str | None = None,
    model: str | None = None,
) -> Dict[str, Any]:
    price = _symbol_price(settings, symbol)
    return create_paper_trade_proposal(
        portfolio_id=portfolio_id,
        symbol=symbol,
        side=side,
        quantity=quantity,
        proposed_price=price,
        reason=reason,
        model=model,
    )


def paper_trade_approve(settings: Settings, proposal_id: str) -> Dict[str, Any]:
    return approve_paper_trade_proposal(settings, proposal_id)


def paper_trade_reject(settings: Settings, proposal_id: str) -> Dict[str, Any]:
    return reject_paper_trade_proposal(proposal_id)
