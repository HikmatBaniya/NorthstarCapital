from __future__ import annotations

import os
import json
from typing import Any, Dict, List
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine



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
