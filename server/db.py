from __future__ import annotations

import os
import json
from typing import Any, Dict, List
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import Settings


def get_engine() -> Engine:
    dsn = os.getenv("POSTGRES_DSN", "").strip()
    if not dsn:
        raise ValueError("POSTGRES_DSN is missing")
    return create_engine(dsn, pool_pre_ping=True)


def memory_put(
    content: str,
    tags: List[str] | None = None,
    conversation_id: str | None = None,
) -> Dict[str, Any]:
    tags = tags or []
    item_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO memory_items (id, content, tags, conversation_id)
                VALUES (:id, :content, :tags, :conversation_id)
                """
            ),
            {
                "id": str(item_id),
                "content": content,
                "tags": tags,
                "conversation_id": conversation_id,
            },
        )
    return {
        "id": str(item_id),
        "content": content,
        "tags": tags,
        "conversation_id": conversation_id,
    }


def memory_search(
    query: str,
    limit: int = 8,
    conversation_id: str | None = None,
) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, content, tags, conversation_id, created_at
                FROM memory_items
                WHERE content_tsv @@ plainto_tsquery('english', :query)
                  AND (:conversation_id IS NULL OR conversation_id = :conversation_id)
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {
                "query": query,
                "limit": limit,
                "conversation_id": conversation_id,
            },
        ).mappings()
        return [dict(row) for row in rows]


def store_research_bundle(
    ticker: str,
    horizon_days: int,
    news_limit: int,
    filings_limit: int,
    bundle: Dict[str, Any],
) -> Dict[str, Any]:
    item_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO research_bundles (id, ticker, horizon_days, news_limit, filings_limit, bundle)
                VALUES (:id, :ticker, :horizon_days, :news_limit, :filings_limit, CAST(:bundle AS jsonb))
                """
            ),
            {
                "id": str(item_id),
                "ticker": ticker,
                "horizon_days": horizon_days,
                "news_limit": news_limit,
                "filings_limit": filings_limit,
                "bundle": json.dumps(bundle),
            },
        )
    return {"id": str(item_id)}


def upsert_research_bundle(
    ticker: str,
    horizon_days: int,
    news_limit: int,
    filings_limit: int,
    bundle: Dict[str, Any],
) -> Dict[str, Any]:
    engine = get_engine()
    with engine.begin() as conn:
        existing = conn.execute(
            text(
                """
                SELECT id FROM research_bundles
                WHERE ticker = :ticker
                LIMIT 1
                """
            ),
            {"ticker": ticker},
        ).mappings().first()
        if existing:
            conn.execute(
                text(
                    """
                    UPDATE research_bundles
                    SET horizon_days = :horizon_days,
                        news_limit = :news_limit,
                        filings_limit = :filings_limit,
                        bundle = CAST(:bundle AS jsonb),
                        created_at = NOW()
                    WHERE id = :id
                    """
                ),
                {
                    "id": existing["id"],
                    "horizon_days": horizon_days,
                    "news_limit": news_limit,
                    "filings_limit": filings_limit,
                    "bundle": json.dumps(bundle),
                },
            )
            return {"id": str(existing["id"]), "updated": True}
    return store_research_bundle(ticker, horizon_days, news_limit, filings_limit, bundle)


def store_report(
    ticker: str,
    horizon_days: int,
    use_llm: bool,
    markdown: str,
    html: str,
) -> Dict[str, Any]:
    item_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO reports (id, ticker, horizon_days, use_llm, markdown, html)
                VALUES (:id, :ticker, :horizon_days, :use_llm, :markdown, :html)
                """
            ),
            {
                "id": str(item_id),
                "ticker": ticker,
                "horizon_days": horizon_days,
                "use_llm": use_llm,
                "markdown": markdown,
                "html": html,
            },
        )
    return {"id": str(item_id)}


def upsert_report(
    ticker: str,
    horizon_days: int,
    use_llm: bool,
    markdown: str,
    html: str,
) -> Dict[str, Any]:
    engine = get_engine()
    with engine.begin() as conn:
        existing = conn.execute(
            text(
                """
                SELECT id FROM reports
                WHERE ticker = :ticker
                LIMIT 1
                """
            ),
            {"ticker": ticker},
        ).mappings().first()
        if existing:
            conn.execute(
                text(
                    """
                    UPDATE reports
                    SET horizon_days = :horizon_days,
                        use_llm = :use_llm,
                        markdown = :markdown,
                        html = :html,
                        created_at = NOW()
                    WHERE id = :id
                    """
                ),
                {
                    "id": existing["id"],
                    "horizon_days": horizon_days,
                    "use_llm": use_llm,
                    "markdown": markdown,
                    "html": html,
                },
            )
            return {"id": str(existing["id"]), "updated": True}
    return store_report(ticker, horizon_days, use_llm, markdown, html)


def store_portfolio(
    name: str,
    symbols: List[str],
    weights: List[float],
    horizon_days: int,
) -> Dict[str, Any]:
    item_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO portfolios (id, name, symbols, weights, horizon_days)
                VALUES (:id, :name, :symbols, :weights, :horizon_days)
                """
            ),
            {
                "id": str(item_id),
                "name": name,
                "symbols": symbols,
                "weights": weights,
                "horizon_days": horizon_days,
            },
        )
    return {"id": str(item_id)}


def upsert_portfolio(
    name: str,
    symbols: List[str],
    weights: List[float],
    horizon_days: int,
) -> Dict[str, Any]:
    engine = get_engine()
    with engine.begin() as conn:
        existing = conn.execute(
            text(
                """
                SELECT id FROM portfolios
                WHERE name = :name
                LIMIT 1
                """
            ),
            {"name": name},
        ).mappings().first()
        if existing:
            conn.execute(
                text(
                    """
                    UPDATE portfolios
                    SET symbols = :symbols,
                        weights = :weights,
                        horizon_days = :horizon_days
                    WHERE id = :id
                    """
                ),
                {
                    "id": existing["id"],
                    "symbols": symbols,
                    "weights": weights,
                    "horizon_days": horizon_days,
                },
            )
            return {"id": str(existing["id"]), "updated": True}
        return store_portfolio(name, symbols, weights, horizon_days)


def store_comparison(
    symbols: List[str],
    start_date: str | None,
    end_date: str | None,
    horizon_days: int,
    result: Dict[str, Any],
) -> Dict[str, Any]:
    item_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO comparisons (id, symbols, start_date, end_date, horizon_days, result)
                VALUES (:id, :symbols, :start_date, :end_date, :horizon_days, CAST(:result AS jsonb))
                """
            ),
            {
                "id": str(item_id),
                "symbols": symbols,
                "start_date": start_date,
                "end_date": end_date,
                "horizon_days": horizon_days,
                "result": json.dumps(result),
            },
        )
    return {"id": str(item_id)}


def latest_research_bundle(ticker: str) -> Dict[str, Any] | None:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, ticker, horizon_days, news_limit, filings_limit, bundle, created_at
                FROM research_bundles
                WHERE ticker = :ticker
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"ticker": ticker},
        ).mappings().first()
        return dict(row) if row else None


def latest_report(ticker: str) -> Dict[str, Any] | None:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, ticker, horizon_days, use_llm, markdown, html, created_at
                FROM reports
                WHERE ticker = :ticker
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"ticker": ticker},
        ).mappings().first()
        return dict(row) if row else None


def list_portfolios() -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, name, symbols, weights, horizon_days, created_at
                FROM portfolios
                ORDER BY created_at DESC
                """
            )
        ).mappings()
        return [dict(row) for row in rows]


def list_research_bundles(limit: int = 100) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, ticker, horizon_days, news_limit, filings_limit, created_at
                FROM research_bundles
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).mappings()
        return [dict(row) for row in rows]


def list_reports(limit: int = 100) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, ticker, horizon_days, use_llm, created_at
                FROM reports
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).mappings()
        return [dict(row) for row in rows]


def list_comparisons(limit: int = 100) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, symbols, start_date, end_date, horizon_days, created_at
                FROM comparisons
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).mappings()
        return [dict(row) for row in rows]


def get_report(report_id: str) -> Dict[str, Any] | None:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, ticker, horizon_days, use_llm, markdown, html, created_at
                FROM reports
                WHERE id = :id
                """
            ),
            {"id": report_id},
        ).mappings().first()
        return dict(row) if row else None


def get_research_bundle(bundle_id: str) -> Dict[str, Any] | None:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, ticker, horizon_days, news_limit, filings_limit, bundle, created_at
                FROM research_bundles
                WHERE id = :id
                """
            ),
            {"id": bundle_id},
        ).mappings().first()
        return dict(row) if row else None


def get_comparison(comparison_id: str) -> Dict[str, Any] | None:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, symbols, start_date, end_date, horizon_days, result, created_at
                FROM comparisons
                WHERE id = :id
                """
            ),
            {"id": comparison_id},
        ).mappings().first()
        return dict(row) if row else None


def latest_comparison(symbols: List[str]) -> Dict[str, Any] | None:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, symbols, start_date, end_date, horizon_days, result, created_at
                FROM comparisons
                WHERE symbols @> :symbols::text[]
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"symbols": symbols},
        ).mappings().first()
        return dict(row) if row else None


def create_conversation(title: str | None = None) -> Dict[str, Any]:
    convo_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO conversations (id, title)
                VALUES (:id, :title)
                """
            ),
            {"id": str(convo_id), "title": title},
        )
    return {"id": str(convo_id)}


def get_conversation(conversation_id: str) -> Dict[str, Any] | None:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, title, created_at
                FROM conversations
                WHERE id = :id
                """
            ),
            {"id": conversation_id},
        ).mappings().first()
        return dict(row) if row else None


def add_message(conversation_id: str, role: str, content: str) -> None:
    msg_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO messages (id, conversation_id, role, content)
                VALUES (:id, :conversation_id, :role, :content)
                """
            ),
            {
                "id": str(msg_id),
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
            },
        )


def list_conversations(limit: int = 50) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, title, created_at
                FROM conversations
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).mappings()
        return [dict(row) for row in rows]


def get_messages(conversation_id: str) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, role, content, created_at
                FROM messages
                WHERE conversation_id = :conversation_id
                ORDER BY created_at ASC
                """
            ),
            {"conversation_id": conversation_id},
        ).mappings()
        return [dict(row) for row in rows]


def delete_conversation(conversation_id: str) -> Dict[str, Any]:
    engine = get_engine()
    with engine.begin() as conn:
        messages_deleted = conn.execute(
            text(
                """
                DELETE FROM messages
                WHERE conversation_id = :conversation_id
                """
            ),
            {"conversation_id": conversation_id},
        ).rowcount or 0
        conv_deleted = conn.execute(
            text(
                """
                DELETE FROM conversations
                WHERE id = :conversation_id
                """
            ),
            {"conversation_id": conversation_id},
        ).rowcount or 0
        return {"conversation_deleted": bool(conv_deleted), "messages_deleted": messages_deleted}


def create_paper_portfolio(
    name: str | None = None, starting_cash: float = 100000.0, currency: str = "NPR"
) -> Dict[str, Any]:
    portfolio_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO paper_portfolios (id, name, base_currency, starting_cash)
                VALUES (:id, :name, :base_currency, :starting_cash)
                RETURNING id, name, base_currency, starting_cash, created_at
                """
            ),
            {
                "id": str(portfolio_id),
                "name": name or "Global Portfolio",
                "base_currency": currency,
                "starting_cash": starting_cash,
            },
        ).mappings().first()
        return dict(row) if row else {"id": str(portfolio_id)}


def list_paper_portfolios(limit: int = 50) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, name, base_currency, starting_cash, created_at
                FROM paper_portfolios
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).mappings()
        return [dict(row) for row in rows]


def get_paper_portfolio(portfolio_id: str) -> Dict[str, Any] | None:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, name, base_currency, starting_cash, created_at
                FROM paper_portfolios
                WHERE id = :id
                """
            ),
            {"id": portfolio_id},
        ).mappings().first()
        return dict(row) if row else None


def get_paper_cash_balance(portfolio_id: str) -> float:
    engine = get_engine()
    with engine.begin() as conn:
        starting = conn.execute(
            text(
                """
                SELECT starting_cash
                FROM paper_portfolios
                WHERE id = :id
                """
            ),
            {"id": portfolio_id},
        ).scalar() or 0
        ledger_sum = conn.execute(
            text(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM paper_cash_ledger
                WHERE portfolio_id = :id
                """
            ),
            {"id": portfolio_id},
        ).scalar() or 0
        buys = conn.execute(
            text(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM paper_trades
                WHERE portfolio_id = :id AND side = 'buy'
                """
            ),
            {"id": portfolio_id},
        ).scalar() or 0
        sells = conn.execute(
            text(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM paper_trades
                WHERE portfolio_id = :id AND side = 'sell'
                """
            ),
            {"id": portfolio_id},
        ).scalar() or 0
        return float(starting) + float(ledger_sum) - float(buys) + float(sells)


def add_paper_cash_ledger(portfolio_id: str, amount: float, reason: str | None = None) -> Dict[str, Any]:
    item_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO paper_cash_ledger (id, portfolio_id, amount, reason)
                VALUES (:id, :portfolio_id, :amount, :reason)
                RETURNING id, portfolio_id, amount, reason, created_at
                """
            ),
            {
                "id": str(item_id),
                "portfolio_id": portfolio_id,
                "amount": amount,
                "reason": reason,
            },
        ).mappings().first()
        return dict(row) if row else {"id": str(item_id)}


def list_paper_positions(portfolio_id: str) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT portfolio_id, symbol, quantity, avg_cost, updated_at
                FROM paper_positions
                WHERE portfolio_id = :portfolio_id
                ORDER BY symbol ASC
                """
            ),
            {"portfolio_id": portfolio_id},
        ).mappings()
        return [dict(row) for row in rows]


def list_paper_trades(portfolio_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, portfolio_id, symbol, side, quantity, price, amount, source, created_at
                FROM paper_trades
                WHERE portfolio_id = :portfolio_id
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"portfolio_id": portfolio_id, "limit": limit},
        ).mappings()
        return [dict(row) for row in rows]


def list_paper_trade_proposals(
    portfolio_id: str, status: str | None = None, limit: int = 200
) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, portfolio_id, symbol, side, quantity, proposed_price, status,
                       reason, model, created_at, updated_at, executed_trade_id, executed_price
                FROM paper_trade_proposals
                WHERE portfolio_id = :portfolio_id
                  AND (:status IS NULL OR status = :status)
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"portfolio_id": portfolio_id, "status": status, "limit": limit},
        ).mappings()
        return [dict(row) for row in rows]


def create_paper_trade_proposal(
    portfolio_id: str,
    symbol: str,
    side: str,
    quantity: float,
    proposed_price: float | None,
    reason: str | None = None,
    model: str | None = None,
) -> Dict[str, Any]:
    proposal_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO paper_trade_proposals (
                    id, portfolio_id, symbol, side, quantity, proposed_price, status, reason, model
                )
                VALUES (
                    :id, :portfolio_id, :symbol, :side, :quantity, :proposed_price, 'pending', :reason, :model
                )
                RETURNING id, portfolio_id, symbol, side, quantity, proposed_price, status,
                          reason, model, created_at, updated_at
                """
            ),
            {
                "id": str(proposal_id),
                "portfolio_id": portfolio_id,
                "symbol": symbol.strip().upper(),
                "side": side.lower(),
                "quantity": quantity,
                "proposed_price": proposed_price,
                "reason": reason,
                "model": model,
            },
        ).mappings().first()
        return dict(row) if row else {"id": str(proposal_id)}


def _apply_paper_trade(
    conn,
    portfolio_id: str,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    source: str,
) -> Dict[str, Any]:
    trade_id = uuid4()
    amount = float(quantity) * float(price)
    row = conn.execute(
        text(
            """
            INSERT INTO paper_trades (id, portfolio_id, symbol, side, quantity, price, amount, source)
            VALUES (:id, :portfolio_id, :symbol, :side, :quantity, :price, :amount, :source)
            RETURNING id, portfolio_id, symbol, side, quantity, price, amount, source, created_at
            """
        ),
        {
            "id": str(trade_id),
            "portfolio_id": portfolio_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "amount": amount,
            "source": source,
        },
    ).mappings().first()

    pos = conn.execute(
        text(
            """
            SELECT quantity, avg_cost
            FROM paper_positions
            WHERE portfolio_id = :portfolio_id AND symbol = :symbol
            """
        ),
        {"portfolio_id": portfolio_id, "symbol": symbol},
    ).mappings().first()

    if side == "buy":
        prev_qty = float(pos["quantity"]) if pos else 0.0
        prev_cost = float(pos["avg_cost"]) if pos else 0.0
        new_qty = prev_qty + quantity
        new_cost = ((prev_qty * prev_cost) + (quantity * price)) / new_qty if new_qty else 0.0
        conn.execute(
            text(
                """
                INSERT INTO paper_positions (portfolio_id, symbol, quantity, avg_cost)
                VALUES (:portfolio_id, :symbol, :quantity, :avg_cost)
                ON CONFLICT (portfolio_id, symbol)
                DO UPDATE SET quantity = EXCLUDED.quantity, avg_cost = EXCLUDED.avg_cost, updated_at = now()
                """
            ),
            {
                "portfolio_id": portfolio_id,
                "symbol": symbol,
                "quantity": new_qty,
                "avg_cost": new_cost,
            },
        )
    else:
        prev_qty = float(pos["quantity"]) if pos else 0.0
        new_qty = max(prev_qty - quantity, 0.0)
        if new_qty == 0.0:
            conn.execute(
                text(
                    """
                    DELETE FROM paper_positions
                    WHERE portfolio_id = :portfolio_id AND symbol = :symbol
                    """
                ),
                {"portfolio_id": portfolio_id, "symbol": symbol},
            )
        else:
            conn.execute(
                text(
                    """
                    UPDATE paper_positions
                    SET quantity = :quantity, updated_at = now()
                    WHERE portfolio_id = :portfolio_id AND symbol = :symbol
                    """
                ),
                {"portfolio_id": portfolio_id, "symbol": symbol, "quantity": new_qty},
            )
    return dict(row) if row else {"id": str(trade_id)}


def approve_paper_trade_proposal(settings: Settings, proposal_id: str) -> Dict[str, Any]:
    engine = get_engine()
    with engine.begin() as conn:
        proposal = conn.execute(
            text(
                """
                SELECT id, portfolio_id, symbol, side, quantity
                FROM paper_trade_proposals
                WHERE id = :id AND status = 'pending'
                """
            ),
            {"id": proposal_id},
        ).mappings().first()
        if not proposal:
            return {"status": "not_found"}
        portfolio_id = proposal["portfolio_id"]
        symbol = proposal["symbol"]
        side = proposal["side"]
        quantity = float(proposal["quantity"] or 0)

        from .tools.nepse_tools import nepse_live_market, nepse_price_volume

        price = None
        for row in nepse_live_market(settings):
            if row.get("symbol") == symbol:
                price = row.get("lastTradedPrice")
                break
        if price is None:
            for row in nepse_price_volume(settings):
                if row.get("symbol") == symbol:
                    price = row.get("lastTradedPrice")
                    break
        if price is None:
            return {"status": "price_unavailable"}
        price = float(price)

        cash = get_paper_cash_balance(portfolio_id)
        if side == "buy" and cash < quantity * price:
            return {"status": "insufficient_cash"}

        trade = _apply_paper_trade(
            conn,
            portfolio_id=portfolio_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            source="paper_approve",
        )
        conn.execute(
            text(
                """
                UPDATE paper_trade_proposals
                SET status = 'approved', executed_trade_id = :trade_id, executed_price = :price, updated_at = now()
                WHERE id = :id
                """
            ),
            {"id": proposal_id, "trade_id": trade["id"], "price": price},
        )
        return {"status": "approved", "trade": trade}


def reject_paper_trade_proposal(proposal_id: str) -> Dict[str, Any]:
    engine = get_engine()
    with engine.begin() as conn:
        updated = conn.execute(
            text(
                """
                UPDATE paper_trade_proposals
                SET status = 'rejected', updated_at = now()
                WHERE id = :id AND status = 'pending'
                """
            ),
            {"id": proposal_id},
        ).rowcount
        return {"status": "rejected" if updated else "not_found"}


def list_watchlist_items() -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, symbol, note, created_at
                FROM watchlist_items
                ORDER BY created_at DESC
                """
            )
        ).mappings()
        return [dict(row) for row in rows]


def upsert_watchlist_item(symbol: str, note: str | None = None) -> Dict[str, Any]:
    item_id = uuid4()
    normalized = symbol.strip().upper()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO watchlist_items (id, symbol, note)
                VALUES (:id, :symbol, :note)
                ON CONFLICT (symbol)
                DO UPDATE SET note = EXCLUDED.note, created_at = NOW()
                RETURNING id, symbol, note, created_at
                """
            ),
            {"id": str(item_id), "symbol": normalized, "note": note},
        ).mappings().first()
        return dict(row) if row else {"id": str(item_id), "symbol": normalized, "note": note}


def remove_watchlist_item(symbol: str) -> bool:
    normalized = symbol.strip().upper()
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                DELETE FROM watchlist_items
                WHERE symbol = :symbol
                """
            ),
            {"symbol": normalized},
        )
        return result.rowcount > 0


def create_company(
    name: str,
    description: str | None = None,
    sector: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    website: str | None = None,
) -> Dict[str, Any]:
    company_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO companies (id, name, description, sector, industry, country, website)
                VALUES (:id, :name, :description, :sector, :industry, :country, :website)
                """
            ),
            {
                "id": str(company_id),
                "name": name,
                "description": description,
                "sector": sector,
                "industry": industry,
                "country": country,
                "website": website,
            },
        )
    return {
        "id": str(company_id),
        "name": name,
        "description": description,
        "sector": sector,
        "industry": industry,
        "country": country,
        "website": website,
    }


def update_company(
    company_id: str,
    name: str | None = None,
    description: str | None = None,
    sector: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    website: str | None = None,
) -> Dict[str, Any] | None:
    engine = get_engine()
    with engine.begin() as conn:
        existing = conn.execute(
            text(
                """
                SELECT id, name, description, sector, industry, country, website
                FROM companies
                WHERE id = :id
                """
            ),
            {"id": company_id},
        ).mappings().first()
        if not existing:
            return None
        updated = {
            "name": name if name is not None else existing["name"],
            "description": description if description is not None else existing["description"],
            "sector": sector if sector is not None else existing["sector"],
            "industry": industry if industry is not None else existing["industry"],
            "country": country if country is not None else existing["country"],
            "website": website if website is not None else existing["website"],
        }
        conn.execute(
            text(
                """
                UPDATE companies
                SET name = :name,
                    description = :description,
                    sector = :sector,
                    industry = :industry,
                    country = :country,
                    website = :website,
                    updated_at = NOW()
                WHERE id = :id
                """
            ),
            {"id": company_id, **updated},
        )
        return {"id": company_id, **updated}


def list_companies(limit: int = 100) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, name, description, sector, industry, country, website, created_at, updated_at
                FROM companies
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).mappings()
        return [dict(row) for row in rows]


def get_company(company_id: str) -> Dict[str, Any] | None:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, name, description, sector, industry, country, website, created_at, updated_at
                FROM companies
                WHERE id = :id
                """
            ),
            {"id": company_id},
        ).mappings().first()
        return dict(row) if row else None


def add_company_identifier(
    company_id: str,
    id_type: str,
    id_value: str,
    source: str | None = None,
) -> Dict[str, Any]:
    identifier_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO company_identifiers (id, company_id, id_type, id_value, source)
                VALUES (:id, :company_id, :id_type, :id_value, :source)
                ON CONFLICT (id_type, id_value)
                DO UPDATE SET company_id = EXCLUDED.company_id, source = EXCLUDED.source
                RETURNING id, company_id, id_type, id_value, source, created_at
                """
            ),
            {
                "id": str(identifier_id),
                "company_id": company_id,
                "id_type": id_type,
                "id_value": id_value,
                "source": source,
            },
        ).mappings().first()
        return dict(row)


def list_company_identifiers(company_id: str) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, company_id, id_type, id_value, source, created_at
                FROM company_identifiers
                WHERE company_id = :company_id
                ORDER BY created_at DESC
                """
            ),
            {"company_id": company_id},
        ).mappings()
        return [dict(row) for row in rows]


def upsert_company_profile(company_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO company_profiles (id, company_id, profile)
                VALUES (:id, :company_id, CAST(:profile AS jsonb))
                ON CONFLICT (company_id)
                DO UPDATE SET profile = CAST(:profile AS jsonb), updated_at = NOW()
                RETURNING id, company_id, profile, updated_at
                """
            ),
            {"id": str(uuid4()), "company_id": company_id, "profile": json.dumps(profile)},
        ).mappings().first()
        return dict(row)


def get_company_profile(company_id: str) -> Dict[str, Any] | None:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, company_id, profile, updated_at
                FROM company_profiles
                WHERE company_id = :company_id
                """
            ),
            {"company_id": company_id},
        ).mappings().first()
        return dict(row) if row else None


def upsert_company_workspace(company_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO company_workspaces (id, company_id, data)
                VALUES (:id, :company_id, CAST(:data AS jsonb))
                ON CONFLICT (company_id)
                DO UPDATE SET data = CAST(:data AS jsonb), updated_at = NOW()
                RETURNING id, company_id, data, updated_at
                """
            ),
            {"id": str(uuid4()), "company_id": company_id, "data": json.dumps(data)},
        ).mappings().first()
        return dict(row)


def get_company_workspace(company_id: str) -> Dict[str, Any] | None:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, company_id, data, updated_at
                FROM company_workspaces
                WHERE company_id = :company_id
                """
            ),
            {"company_id": company_id},
        ).mappings().first()
        return dict(row) if row else None


def add_company_person(
    company_id: str,
    name: str,
    role: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    bio: str | None = None,
    source: str | None = None,
) -> Dict[str, Any]:
    person_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        existing = conn.execute(
            text(
                """
                SELECT id, company_id, name, role, start_date, end_date, bio, source, created_at
                FROM company_people
                WHERE company_id = :company_id
                  AND name = :name
                  AND COALESCE(role, '') = COALESCE(:role, '')
                LIMIT 1
                """
            ),
            {"company_id": company_id, "name": name, "role": role},
        ).mappings().first()
        if existing:
            return dict(existing)
        row = conn.execute(
            text(
                """
                INSERT INTO company_people (id, company_id, name, role, start_date, end_date, bio, source)
                VALUES (:id, :company_id, :name, :role, :start_date, :end_date, :bio, :source)
                RETURNING id, company_id, name, role, start_date, end_date, bio, source, created_at
                """
            ),
            {
                "id": str(person_id),
                "company_id": company_id,
                "name": name,
                "role": role,
                "start_date": start_date,
                "end_date": end_date,
                "bio": bio,
                "source": source,
            },
        ).mappings().first()
        return dict(row)


def list_company_people(company_id: str) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, company_id, name, role, start_date, end_date, bio, source, created_at
                FROM company_people
                WHERE company_id = :company_id
                ORDER BY created_at DESC
                """
            ),
            {"company_id": company_id},
        ).mappings()
        return [dict(row) for row in rows]


def add_entity_image(
    entity_type: str,
    entity_id: str,
    image_url: str,
    local_path: str | None = None,
    license: str | None = None,
    attribution: str | None = None,
    source: str | None = None,
) -> Dict[str, Any]:
    image_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        existing = conn.execute(
            text(
                """
                SELECT id, entity_type, entity_id, image_url, local_path, license, attribution, source, created_at
                FROM company_images
                WHERE entity_type = :entity_type AND entity_id = :entity_id AND image_url = :image_url
                LIMIT 1
                """
            ),
            {"entity_type": entity_type, "entity_id": entity_id, "image_url": image_url},
        ).mappings().first()
        if existing:
            return dict(existing)
        row = conn.execute(
            text(
                """
                INSERT INTO company_images (
                    id, entity_type, entity_id, image_url, local_path, license, attribution, source
                )
                VALUES (:id, :entity_type, :entity_id, :image_url, :local_path, :license, :attribution, :source)
                RETURNING id, entity_type, entity_id, image_url, local_path, license, attribution, source, created_at
                """
            ),
            {
                "id": str(image_id),
                "entity_type": entity_type,
                "entity_id": entity_id,
                "image_url": image_url,
                "local_path": local_path,
                "license": license,
                "attribution": attribution,
                "source": source,
            },
        ).mappings().first()
        return dict(row)


def list_entity_images(entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, entity_type, entity_id, image_url, local_path, license, attribution, source, created_at
                FROM company_images
                WHERE entity_type = :entity_type AND entity_id = :entity_id
                ORDER BY created_at DESC
                """
            ),
            {"entity_type": entity_type, "entity_id": entity_id},
        ).mappings()
        return [dict(row) for row in rows]


def add_company_document(
    company_id: str,
    doc_type: str | None,
    title: str | None,
    url: str | None,
    content: str | None,
    source: str | None,
    published_at: str | None,
) -> Dict[str, Any]:
    doc_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        if url:
            existing = conn.execute(
                text(
                    """
                    SELECT id, company_id, doc_type, title, url, source, published_at, created_at
                    FROM company_documents
                    WHERE company_id = :company_id AND url = :url
                    LIMIT 1
                    """
                ),
                {"company_id": company_id, "url": url},
            ).mappings().first()
            if existing:
                return dict(existing)
        row = conn.execute(
            text(
                """
                INSERT INTO company_documents (
                    id, company_id, doc_type, title, url, content, source, published_at
                )
                VALUES (:id, :company_id, :doc_type, :title, :url, :content, :source, :published_at)
                RETURNING id, company_id, doc_type, title, url, source, published_at, created_at
                """
            ),
            {
                "id": str(doc_id),
                "company_id": company_id,
                "doc_type": doc_type,
                "title": title,
                "url": url,
                "content": content,
                "source": source,
                "published_at": published_at,
            },
        ).mappings().first()
        return dict(row)


def list_company_documents(company_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, company_id, doc_type, title, url, source, published_at, created_at
                FROM company_documents
                WHERE company_id = :company_id
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"company_id": company_id, "limit": limit},
        ).mappings()
        return [dict(row) for row in rows]


def add_company_financial(
    company_id: str,
    metric: str,
    value: float | None,
    period_start: str | None = None,
    period_end: str | None = None,
    unit: str | None = None,
    currency: str | None = None,
    source: str | None = None,
) -> Dict[str, Any]:
    item_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        existing = conn.execute(
            text(
                """
                SELECT id, company_id, metric, value, period_start, period_end, unit, currency, source, created_at
                FROM company_financials
                WHERE company_id = :company_id
                  AND metric = :metric
                  AND COALESCE(period_end::text, '') = COALESCE(:period_end, '')
                  AND COALESCE(unit, '') = COALESCE(:unit, '')
                LIMIT 1
                """
            ),
            {
                "company_id": company_id,
                "metric": metric,
                "period_end": period_end,
                "unit": unit,
            },
        ).mappings().first()
        if existing:
            return dict(existing)
        row = conn.execute(
            text(
                """
                INSERT INTO company_financials (
                    id, company_id, metric, value, period_start, period_end, unit, currency, source
                )
                VALUES (
                    :id, :company_id, :metric, :value, :period_start, :period_end, :unit, :currency, :source
                )
                RETURNING id, company_id, metric, value, period_start, period_end, unit, currency, source, created_at
                """
            ),
            {
                "id": str(item_id),
                "company_id": company_id,
                "metric": metric,
                "value": value,
                "period_start": period_start,
                "period_end": period_end,
                "unit": unit,
                "currency": currency,
                "source": source,
            },
        ).mappings().first()
        return dict(row)


def list_company_financials(
    company_id: str,
    metric: str | None = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        if metric:
            rows = conn.execute(
                text(
                    """
                    SELECT id, company_id, metric, value, period_start, period_end, unit, currency, source, created_at
                    FROM company_financials
                    WHERE company_id = :company_id AND metric = :metric
                    ORDER BY period_end DESC NULLS LAST
                    LIMIT :limit
                    """
                ),
                {"company_id": company_id, "metric": metric, "limit": limit},
            ).mappings()
        else:
            rows = conn.execute(
                text(
                    """
                    SELECT id, company_id, metric, value, period_start, period_end, unit, currency, source, created_at
                    FROM company_financials
                    WHERE company_id = :company_id
                    ORDER BY period_end DESC NULLS LAST
                    LIMIT :limit
                    """
                ),
                {"company_id": company_id, "limit": limit},
            ).mappings()
        return [dict(row) for row in rows]


def add_company_subsidiary(
    company_id: str,
    name: str,
    country: str | None = None,
    ownership_pct: float | None = None,
    source: str | None = None,
) -> Dict[str, Any]:
    item_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        existing = conn.execute(
            text(
                """
                SELECT id, company_id, name, country, ownership_pct, source, created_at
                FROM company_subsidiaries
                WHERE company_id = :company_id AND name = :name AND COALESCE(source, '') = COALESCE(:source, '')
                LIMIT 1
                """
            ),
            {"company_id": company_id, "name": name, "source": source},
        ).mappings().first()
        if existing:
            return dict(existing)
        row = conn.execute(
            text(
                """
                INSERT INTO company_subsidiaries (id, company_id, name, country, ownership_pct, source)
                VALUES (:id, :company_id, :name, :country, :ownership_pct, :source)
                RETURNING id, company_id, name, country, ownership_pct, source, created_at
                """
            ),
            {
                "id": str(item_id),
                "company_id": company_id,
                "name": name,
                "country": country,
                "ownership_pct": ownership_pct,
                "source": source,
            },
        ).mappings().first()
        return dict(row)


def list_company_subsidiaries(company_id: str) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, company_id, name, country, ownership_pct, source, created_at
                FROM company_subsidiaries
                WHERE company_id = :company_id
                ORDER BY name ASC
                """
            ),
            {"company_id": company_id},
        ).mappings()
        return [dict(row) for row in rows]


def add_company_ownership(
    company_id: str,
    holder_name: str,
    holder_type: str | None = None,
    percent: float | None = None,
    shares: float | None = None,
    as_of_date: str | None = None,
    source: str | None = None,
) -> Dict[str, Any]:
    item_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        existing = conn.execute(
            text(
                """
                SELECT id, company_id, holder_name, holder_type, percent, shares, as_of_date, source, created_at
                FROM company_ownership
                WHERE company_id = :company_id
                  AND holder_name = :holder_name
                  AND COALESCE(as_of_date::text, '') = COALESCE(:as_of_date, '')
                LIMIT 1
                """
            ),
            {"company_id": company_id, "holder_name": holder_name, "as_of_date": as_of_date},
        ).mappings().first()
        if existing:
            return dict(existing)
        row = conn.execute(
            text(
                """
                INSERT INTO company_ownership (
                    id, company_id, holder_name, holder_type, percent, shares, as_of_date, source
                )
                VALUES (
                    :id, :company_id, :holder_name, :holder_type, :percent, :shares, :as_of_date, :source
                )
                RETURNING id, company_id, holder_name, holder_type, percent, shares, as_of_date, source, created_at
                """
            ),
            {
                "id": str(item_id),
                "company_id": company_id,
                "holder_name": holder_name,
                "holder_type": holder_type,
                "percent": percent,
                "shares": shares,
                "as_of_date": as_of_date,
                "source": source,
            },
        ).mappings().first()
        return dict(row)


def list_company_ownership(company_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, company_id, holder_name, holder_type, percent, shares, as_of_date, source, created_at
                FROM company_ownership
                WHERE company_id = :company_id
                ORDER BY as_of_date DESC NULLS LAST, percent DESC NULLS LAST
                LIMIT :limit
                """
            ),
            {"company_id": company_id, "limit": limit},
        ).mappings()
        return [dict(row) for row in rows]


def touch_company(company_id: str) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE companies
                SET updated_at = NOW()
                WHERE id = :id
                """
            ),
            {"id": company_id},
        )


def list_stale_companies(min_age_seconds: int, limit: int = 50) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, name, description, sector, industry, country, website, created_at, updated_at
                FROM companies
                WHERE updated_at < NOW() - (:min_age_seconds || ' seconds')::interval
                ORDER BY updated_at ASC
                LIMIT :limit
                """
            ),
            {"min_age_seconds": min_age_seconds, "limit": limit},
        ).mappings()
        return [dict(row) for row in rows]


def create_shelf(
    name: str,
    description: str | None = None,
    sort_order: int = 0,
) -> Dict[str, Any]:
    shelf_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO shelves (id, name, description, sort_order)
                VALUES (:id, :name, :description, :sort_order)
                ON CONFLICT (name)
                DO UPDATE SET description = EXCLUDED.description, sort_order = EXCLUDED.sort_order
                RETURNING id, name, description, sort_order, created_at
                """
            ),
            {
                "id": str(shelf_id),
                "name": name,
                "description": description,
                "sort_order": sort_order,
            },
        ).mappings().first()
        return dict(row)


def list_shelves() -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, name, description, sort_order, created_at
                FROM shelves
                ORDER BY sort_order ASC, created_at DESC
                """
            )
        ).mappings()
        return [dict(row) for row in rows]


def store_analyst_run(
    market: str,
    symbol: str,
    request: Dict[str, Any],
    brief: Dict[str, Any],
    analysis: Dict[str, Any],
) -> Dict[str, Any]:
    item_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO analyst_runs (id, market, symbol, request, brief, analysis)
                VALUES (:id, :market, :symbol, CAST(:request AS jsonb), CAST(:brief AS jsonb), CAST(:analysis AS jsonb))
                """
            ),
            {
                "id": str(item_id),
                "market": market,
                "symbol": symbol,
                "request": json.dumps(request),
                "brief": json.dumps(brief),
                "analysis": json.dumps(analysis),
            },
        )
    return {"id": str(item_id)}


def get_analyst_run(run_id: str) -> Dict[str, Any] | None:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, market, symbol, request, brief, analysis, created_at
                FROM analyst_runs
                WHERE id = :id
                """
            ),
            {"id": run_id},
        ).mappings().first()
        return dict(row) if row else None


def add_shelf_item(shelf_id: str, company_id: str, sort_order: int = 0) -> Dict[str, Any]:
    item_id = uuid4()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO shelf_items (id, shelf_id, company_id, sort_order)
                VALUES (:id, :shelf_id, :company_id, :sort_order)
                ON CONFLICT (shelf_id, company_id)
                DO UPDATE SET sort_order = EXCLUDED.sort_order
                RETURNING id, shelf_id, company_id, sort_order, created_at
                """
            ),
            {
                "id": str(item_id),
                "shelf_id": shelf_id,
                "company_id": company_id,
                "sort_order": sort_order,
            },
        ).mappings().first()
        return dict(row)


def list_shelf_items(shelf_id: str) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT si.id, si.shelf_id, si.company_id, si.sort_order, si.created_at,
                       c.name, c.sector, c.industry, c.country, c.website
                FROM shelf_items si
                JOIN companies c ON c.id = si.company_id
                WHERE si.shelf_id = :shelf_id
                ORDER BY si.sort_order ASC, si.created_at DESC
                """
            ),
            {"shelf_id": shelf_id},
        ).mappings()
        return [dict(row) for row in rows]
