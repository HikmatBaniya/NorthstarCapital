from typing import Any, Dict
import os
import threading
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from .config import load_settings
from .llm_agent import chat_with_tools
from .enrichment import enrich_company_data, extract_financials_from_sec
from .citadel_agent import apply_actions, build_context, generate_actions, normalize_actions
from .tool_registry import TOOLS
from .tool_dispatch import dispatch_tool
from .research import build_research_bundle
from .reporting import generate_report
from .analytics import compare_prices, portfolio_stats
from .extensions import get_extension
from .db import (
    store_research_bundle,
    store_report,
    store_portfolio,
    upsert_portfolio,
    store_comparison,
    latest_research_bundle,
    latest_report,
    list_portfolios,
    latest_comparison,
    create_conversation,
    get_conversation,
    add_message,
    list_conversations,
    get_messages,
    list_research_bundles,
    list_reports,
    list_comparisons,
    get_report,
    get_research_bundle,
    get_comparison,
    upsert_research_bundle,
    upsert_report,
    list_watchlist_items,
    upsert_watchlist_item,
    remove_watchlist_item,
    create_company,
    update_company,
    list_companies,
    get_company,
    add_company_identifier,
    list_company_identifiers,
    upsert_company_profile,
    get_company_profile,
    upsert_company_workspace,
    get_company_workspace,
    add_company_person,
    list_company_people,
    add_entity_image,
    list_entity_images,
    add_company_document,
    list_company_documents,
    create_shelf,
    list_shelves,
    add_shelf_item,
    list_shelf_items,
    touch_company,
    list_stale_companies,
    add_company_financial,
    list_company_financials,
    add_company_subsidiary,
    list_company_subsidiaries,
    add_company_ownership,
    list_company_ownership,
)

load_dotenv()

app = FastAPI(title="Financial MCP Server", version="0.1.0")
settings = load_settings()
_extension = get_extension()
if _extension and hasattr(_extension, "register_routes"):
    try:
        _extension.register_routes(app)
    except Exception:
        pass
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if not origins:
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    name: str
    result: Any


class ChatRequest(BaseModel):
    message: str
    history: list[Dict[str, str]] = []
    use_memory: bool = True
    store_memory: bool = False
    conversation_id: str | None = None
    title: str | None = None
    explore_links: bool = True


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str




class ResearchRequest(BaseModel):
    ticker: str
    horizon_days: int = 365
    news_limit: int = 6
    filings_limit: int = 5


class ReportRequest(BaseModel):
    ticker: str
    horizon_days: int = 365
    use_llm: bool = True


class CompareRequest(BaseModel):
    symbols: list[str]
    start: str | None = None
    end: str | None = None
    horizon_days: int = 365


class PortfolioRequest(BaseModel):
    symbols: list[str]
    weights: list[float]
    start: str | None = None
    end: str | None = None
    horizon_days: int = 365
    name: str | None = None


class LatestRequest(BaseModel):
    ticker: str


class ComparisonLatestRequest(BaseModel):
    symbols: list[str]


class WatchlistRequest(BaseModel):
    symbol: str
    note: str | None = None


class IdentifierInput(BaseModel):
    id_type: str
    id_value: str
    source: str | None = None


class CompanyCreateRequest(BaseModel):
    name: str
    description: str | None = None
    sector: str | None = None
    industry: str | None = None
    country: str | None = None
    website: str | None = None
    identifiers: list[IdentifierInput] = []
    profile: Dict[str, Any] | None = None


class CompanyUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    sector: str | None = None
    industry: str | None = None
    country: str | None = None
    website: str | None = None


class CompanyProfileRequest(BaseModel):
    profile: Dict[str, Any]


class CompanyWorkspaceRequest(BaseModel):
    data: Dict[str, Any]


class CompanyPersonRequest(BaseModel):
    name: str
    role: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    bio: str | None = None
    source: str | None = None


class CompanyImageRequest(BaseModel):
    entity_type: str
    entity_id: str
    image_url: str
    local_path: str | None = None
    license: str | None = None
    attribution: str | None = None
    source: str | None = None


class CompanyDocumentRequest(BaseModel):
    doc_type: str | None = None
    title: str | None = None
    url: str | None = None
    content: str | None = None
    source: str | None = None
    published_at: str | None = None


class CompanyFinancialRequest(BaseModel):
    metric: str
    value: float | None = None
    period_start: str | None = None
    period_end: str | None = None
    unit: str | None = None
    currency: str | None = None
    source: str | None = None


class CompanySubsidiaryRequest(BaseModel):
    name: str
    country: str | None = None
    ownership_pct: float | None = None
    source: str | None = None


class CompanyOwnershipRequest(BaseModel):
    holder_name: str
    holder_type: str | None = None
    percent: float | None = None
    shares: float | None = None
    as_of_date: str | None = None
    source: str | None = None


class ShelfCreateRequest(BaseModel):
    name: str
    description: str | None = None
    sort_order: int = 0


class ShelfItemRequest(BaseModel):
    company_id: str
    sort_order: int = 0


class EnrichResponse(BaseModel):
    status: str
    updated: bool
    sources: list[str]


class CitadelAgentRequest(BaseModel):
    company_id: str
    instruction: str
    mode: str = "auto"  # auto | propose
    model: str | None = None
    allow_web: bool = True


class CitadelAgentApplyRequest(BaseModel):
    company_id: str
    actions: list[Dict[str, Any]]


def _apply_company_enrichment(company_id: str, settings) -> Dict[str, Any]:
    company = get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="not_found")
    data = enrich_company_data(settings, company["name"])
    company_fields = data.get("company", {})

    update_company(
        company_id,
        name=company_fields.get("name") or company["name"],
        description=company_fields.get("description") or company.get("description"),
        sector=company_fields.get("sector") or company.get("sector"),
        industry=company_fields.get("industry") or company.get("industry"),
        country=company_fields.get("country") or company.get("country"),
        website=company_fields.get("website") or company.get("website"),
    )

    profile = data.get("profile") or {}
    coverage = data.get("coverage")
    if coverage:
        profile["coverage"] = coverage
    if profile:
        upsert_company_profile(company_id, profile)

    for ident in data.get("identifiers", []):
        id_value = ident.get("id_value")
        if not id_value:
            continue
        add_company_identifier(
            company_id=company_id,
            id_type=ident.get("id_type", "unknown"),
            id_value=id_value,
            source=ident.get("source"),
        )

    for person in data.get("people", []):
        person_row = add_company_person(
            company_id=company_id,
            name=person.get("name", ""),
            role=person.get("role"),
            source=person.get("source"),
        )
        image_url = person.get("image")
        if image_url and person_row:
            add_entity_image(
                entity_type="person",
                entity_id=person_row["id"],
                image_url=image_url,
                license="Wikimedia Commons",
                attribution="Wikidata",
                source=person.get("source"),
            )

    for image in data.get("images", []):
        add_entity_image(
            entity_type=image.get("entity_type", "company"),
            entity_id=company_id,
            image_url=image.get("image_url", ""),
            license=image.get("license"),
            attribution=image.get("attribution"),
            source=image.get("source"),
        )

    for doc in data.get("documents", []):
        add_company_document(
            company_id=company_id,
            doc_type=doc.get("doc_type"),
            title=doc.get("title"),
            url=doc.get("url"),
            content=doc.get("content"),
            source=doc.get("source"),
            published_at=doc.get("published_at"),
        )

    for subsidiary in data.get("subsidiaries", []):
        name = subsidiary.get("name")
        if not name:
            continue
        add_company_subsidiary(
            company_id=company_id,
            name=name,
            country=subsidiary.get("country"),
            ownership_pct=subsidiary.get("ownership_pct"),
            source=subsidiary.get("source"),
        )

    for holder in data.get("ownership", []):
        holder_name = holder.get("holder_name")
        if not holder_name:
            continue
        add_company_ownership(
            company_id=company_id,
            holder_name=holder_name,
            holder_type=holder.get("holder_type"),
            percent=holder.get("percent"),
            shares=holder.get("shares"),
            as_of_date=holder.get("as_of_date"),
            source=holder.get("source"),
        )

    ticker = None
    profile = data.get("profile") or {}
    if profile.get("ticker"):
        ticker = profile.get("ticker")
    if not ticker:
        for ident in data.get("identifiers", []):
            if ident.get("id_type") == "ticker":
                ticker = ident.get("id_value")
                break
    if ticker:
        for row in extract_financials_from_sec(settings, ticker):
            add_company_financial(
                company_id=company_id,
                metric=row.get("metric", ""),
                value=row.get("value"),
                period_start=row.get("period_start"),
                period_end=row.get("period_end"),
                unit=row.get("unit"),
                currency=row.get("currency"),
                source=row.get("source"),
            )

    touch_company(company_id)
    return {"status": "ok", "updated": True, "sources": ["wikidata", "duckduckgo"]}


def _refresh_stale_companies(settings) -> None:
    min_age = settings.citadel_refresh_interval_seconds
    candidates = list_stale_companies(min_age_seconds=min_age, limit=25)
    for company in candidates:
        try:
            _apply_company_enrichment(company["id"], settings)
        except Exception:
            continue


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/tools")
def list_tools() -> Dict[str, Any]:
    return {
        "tools": [
            {"name": t.name, "description": t.description, "input_schema": t.input_schema}
            for t in TOOLS
        ]
    }


@app.post("/invoke", response_model=ToolResult)
def invoke_tool(call: ToolCall) -> ToolResult:
    settings = load_settings()
    try:
        result = dispatch_tool(settings, call.name, call.arguments)
        return ToolResult(name=call.name, result=result)
    except HTTPException:
        raise
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    settings = load_settings()
    if not settings.groq_api_key:
        raise HTTPException(status_code=400, detail="GROQ_API_KEY is missing")
    try:
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation = create_conversation(request.title)
            conversation_id = conversation["id"]
        else:
            existing = get_conversation(conversation_id)
            if not existing:
                conversation = create_conversation(request.title)
                conversation_id = conversation["id"]
        if request.history:
            history = request.history
        else:
            history = [
                {"role": row.get("role", ""), "content": row.get("content", "")}
                for row in get_messages(conversation_id)
            ]
        if len(history) > 50:
            history = history[-50:]
        add_message(conversation_id, "user", request.message)
        reply = chat_with_tools(
            message=request.message,
            history=history,
            use_memory=request.use_memory,
            store_memory=request.store_memory,
            settings=settings,
            conversation_id=conversation_id,
            explore_links=request.explore_links,
        )
        add_message(conversation_id, "assistant", reply)
        return ChatResponse(reply=reply, conversation_id=conversation_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc




@app.post("/research")
def research_endpoint(request: ResearchRequest) -> Dict[str, Any]:
    settings = load_settings()
    try:
        bundle = build_research_bundle(
            settings,
            request.ticker,
            horizon_days=request.horizon_days,
            news_limit=request.news_limit,
            filings_limit=request.filings_limit,
        )
        upsert_research_bundle(
            request.ticker,
            request.horizon_days,
            request.news_limit,
            request.filings_limit,
            bundle,
        )
        return bundle
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/report")
def report_endpoint(request: ReportRequest) -> Dict[str, Any]:
    settings = load_settings()
    try:
        bundle = build_research_bundle(settings, request.ticker, horizon_days=request.horizon_days)
        report = generate_report(bundle, use_llm=request.use_llm)
        upsert_report(
            request.ticker,
            request.horizon_days,
            request.use_llm,
            report["markdown"],
            report["html"],
        )
        return report
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc




@app.post("/compare")
def compare_endpoint(request: CompareRequest) -> Dict[str, Any]:
    settings = load_settings()
    try:
        result = compare_prices(
            settings,
            request.symbols,
            start=request.start,
            end=request.end,
            horizon_days=request.horizon_days,
        )
        store_comparison(
            request.symbols,
            request.start,
            request.end,
            request.horizon_days,
            result,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/portfolio")
def portfolio_endpoint(request: PortfolioRequest) -> Dict[str, Any]:
    settings = load_settings()
    try:
        result = portfolio_stats(
            settings,
            symbols=request.symbols,
            weights=request.weights,
            start=request.start,
            end=request.end,
            horizon_days=request.horizon_days,
        )
        if request.name:
            upsert_portfolio(
                request.name, request.symbols, request.weights, request.horizon_days
            )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/research/latest")
def research_latest(request: LatestRequest) -> Dict[str, Any]:
    item = latest_research_bundle(request.ticker)
    if not item:
        raise HTTPException(status_code=404, detail="not_found")
    return item


@app.post("/report/latest")
def report_latest(request: LatestRequest) -> Dict[str, Any]:
    item = latest_report(request.ticker)
    if not item:
        raise HTTPException(status_code=404, detail="not_found")
    return item


@app.get("/portfolios")
def portfolios_list() -> Dict[str, Any]:
    return {"portfolios": list_portfolios()}


@app.post("/compare/latest")
def compare_latest(request: ComparisonLatestRequest) -> Dict[str, Any]:
    item = latest_comparison(request.symbols)
    if not item:
        raise HTTPException(status_code=404, detail="not_found")
    return item


@app.get("/research")
def research_list() -> Dict[str, Any]:
    return {"research": list_research_bundles()}


@app.get("/reports")
def reports_list() -> Dict[str, Any]:
    return {"reports": list_reports()}


@app.get("/comparisons")
def comparisons_list() -> Dict[str, Any]:
    return {"comparisons": list_comparisons()}


@app.get("/reports/{report_id}")
def report_get(report_id: str) -> Dict[str, Any]:
    item = get_report(report_id)
    if not item:
        raise HTTPException(status_code=404, detail="not_found")
    return item


@app.get("/research/{bundle_id}")
def research_get(bundle_id: str) -> Dict[str, Any]:
    item = get_research_bundle(bundle_id)
    if not item:
        raise HTTPException(status_code=404, detail="not_found")
    return item


@app.get("/comparisons/{comparison_id}")
def comparison_get(comparison_id: str) -> Dict[str, Any]:
    item = get_comparison(comparison_id)
    if not item:
        raise HTTPException(status_code=404, detail="not_found")
    return item


@app.get("/conversations")
def conversations_list() -> Dict[str, Any]:
    return {"conversations": list_conversations()}


@app.get("/conversations/{conversation_id}")
def conversations_messages(conversation_id: str) -> Dict[str, Any]:
    return {"messages": get_messages(conversation_id)}


@app.get("/watchlist")
def watchlist_list() -> Dict[str, Any]:
    return {"items": list_watchlist_items()}


@app.post("/watchlist")
def watchlist_add(request: WatchlistRequest) -> Dict[str, Any]:
    if not request.symbol.strip():
        raise HTTPException(status_code=400, detail="symbol_required")
    return upsert_watchlist_item(request.symbol, request.note)


@app.delete("/watchlist/{symbol}")
def watchlist_remove(symbol: str) -> Dict[str, Any]:
    if not symbol.strip():
        raise HTTPException(status_code=400, detail="symbol_required")
    deleted = remove_watchlist_item(symbol)
    return {"deleted": deleted}


@app.post("/companies")
def companies_create(request: CompanyCreateRequest) -> Dict[str, Any]:
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="name_required")
    company = create_company(
        name=request.name.strip(),
        description=request.description,
        sector=request.sector,
        industry=request.industry,
        country=request.country,
        website=request.website,
    )
    for ident in request.identifiers:
        add_company_identifier(
            company_id=company["id"],
            id_type=ident.id_type,
            id_value=ident.id_value,
            source=ident.source,
        )
    if request.profile is not None:
        upsert_company_profile(company["id"], request.profile)
    try:
        _apply_company_enrichment(company["id"], settings)
    except Exception:
        return company
    enriched = get_company(company["id"])
    return enriched or company


@app.get("/companies")
def companies_list(limit: int = 100) -> Dict[str, Any]:
    return {"companies": list_companies(limit=limit)}


@app.get("/companies/{company_id}")
def companies_get(company_id: str) -> Dict[str, Any]:
    company = get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="not_found")
    try:
        _apply_company_enrichment(company_id, settings)
    except Exception:
        return {
            "company": company,
            "identifiers": list_company_identifiers(company_id),
            "profile": get_company_profile(company_id),
            "people": list_company_people(company_id),
            "images": list_entity_images("company", company_id),
        }
    company = get_company(company_id) or company
    return {
        "company": company,
        "identifiers": list_company_identifiers(company_id),
        "profile": get_company_profile(company_id),
        "people": list_company_people(company_id),
        "images": list_entity_images("company", company_id),
    }


@app.put("/companies/{company_id}")
def companies_update(company_id: str, request: CompanyUpdateRequest) -> Dict[str, Any]:
    company = update_company(
        company_id,
        name=request.name,
        description=request.description,
        sector=request.sector,
        industry=request.industry,
        country=request.country,
        website=request.website,
    )
    if not company:
        raise HTTPException(status_code=404, detail="not_found")
    return company


@app.post("/companies/{company_id}/profile")
def companies_profile_upsert(company_id: str, request: CompanyProfileRequest) -> Dict[str, Any]:
    company = get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="not_found")
    return upsert_company_profile(company_id, request.profile)


@app.get("/companies/{company_id}/profile")
def companies_profile_get(company_id: str) -> Dict[str, Any]:
    profile = get_company_profile(company_id)
    if not profile:
        raise HTTPException(status_code=404, detail="not_found")
    return profile


@app.put("/companies/{company_id}/workspace")
def companies_workspace_upsert(company_id: str, request: CompanyWorkspaceRequest) -> Dict[str, Any]:
    company = get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="not_found")
    return upsert_company_workspace(company_id, request.data)


@app.get("/companies/{company_id}/workspace")
def companies_workspace_get(company_id: str) -> Dict[str, Any]:
    workspace = get_company_workspace(company_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="not_found")
    return workspace


@app.post("/companies/{company_id}/people")
def companies_people_add(company_id: str, request: CompanyPersonRequest) -> Dict[str, Any]:
    company = get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="not_found")
    return add_company_person(
        company_id=company_id,
        name=request.name,
        role=request.role,
        start_date=request.start_date,
        end_date=request.end_date,
        bio=request.bio,
        source=request.source,
    )


@app.get("/companies/{company_id}/people")
def companies_people_list(company_id: str) -> Dict[str, Any]:
    return {"people": list_company_people(company_id)}


@app.post("/images")
def images_add(request: CompanyImageRequest) -> Dict[str, Any]:
    return add_entity_image(
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        image_url=request.image_url,
        local_path=request.local_path,
        license=request.license,
        attribution=request.attribution,
        source=request.source,
    )


@app.get("/images")
def images_list(entity_type: str, entity_id: str) -> Dict[str, Any]:
    return {"images": list_entity_images(entity_type, entity_id)}


@app.post("/companies/{company_id}/documents")
def companies_documents_add(company_id: str, request: CompanyDocumentRequest) -> Dict[str, Any]:
    company = get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="not_found")
    return add_company_document(
        company_id=company_id,
        doc_type=request.doc_type,
        title=request.title,
        url=request.url,
        content=request.content,
        source=request.source,
        published_at=request.published_at,
    )


@app.get("/companies/{company_id}/documents")
def companies_documents_list(company_id: str, limit: int = 100) -> Dict[str, Any]:
    return {"documents": list_company_documents(company_id, limit=limit)}


@app.post("/companies/{company_id}/financials")
def companies_financials_add(company_id: str, request: CompanyFinancialRequest) -> Dict[str, Any]:
    company = get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="not_found")
    return add_company_financial(
        company_id=company_id,
        metric=request.metric,
        value=request.value,
        period_start=request.period_start,
        period_end=request.period_end,
        unit=request.unit,
        currency=request.currency,
        source=request.source,
    )


@app.get("/companies/{company_id}/financials")
def companies_financials_list(company_id: str, metric: str | None = None, limit: int = 200) -> Dict[str, Any]:
    return {"financials": list_company_financials(company_id, metric=metric, limit=limit)}


@app.post("/companies/{company_id}/subsidiaries")
def companies_subsidiaries_add(company_id: str, request: CompanySubsidiaryRequest) -> Dict[str, Any]:
    company = get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="not_found")
    return add_company_subsidiary(
        company_id=company_id,
        name=request.name,
        country=request.country,
        ownership_pct=request.ownership_pct,
        source=request.source,
    )


@app.get("/companies/{company_id}/subsidiaries")
def companies_subsidiaries_list(company_id: str) -> Dict[str, Any]:
    return {"subsidiaries": list_company_subsidiaries(company_id)}


@app.post("/companies/{company_id}/ownership")
def companies_ownership_add(company_id: str, request: CompanyOwnershipRequest) -> Dict[str, Any]:
    company = get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="not_found")
    return add_company_ownership(
        company_id=company_id,
        holder_name=request.holder_name,
        holder_type=request.holder_type,
        percent=request.percent,
        shares=request.shares,
        as_of_date=request.as_of_date,
        source=request.source,
    )


@app.get("/companies/{company_id}/ownership")
def companies_ownership_list(company_id: str, limit: int = 200) -> Dict[str, Any]:
    return {"ownership": list_company_ownership(company_id, limit=limit)}


@app.post("/companies/{company_id}/enrich", response_model=EnrichResponse)
def companies_enrich(company_id: str) -> Dict[str, Any]:
    return _apply_company_enrichment(company_id, settings)


@app.post("/citadel/agent")
def citadel_agent(request: CitadelAgentRequest) -> Dict[str, Any]:
    company = get_company(request.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="not_found")
    context = build_context(request.company_id)
    try:
        result = generate_actions(
            settings,
            request.instruction,
            context,
            model_override=request.model,
            allow_web=request.allow_web,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    actions = normalize_actions(result.get("actions", []))
    if request.mode == "auto":
        workspace = apply_actions(request.company_id, actions)
        return {"mode": "auto", "summary": result.get("summary", ""), "actions": actions, "workspace": workspace}
    return {"mode": "propose", "summary": result.get("summary", ""), "actions": actions}


@app.post("/citadel/agent/apply")
def citadel_agent_apply(request: CitadelAgentApplyRequest) -> Dict[str, Any]:
    company = get_company(request.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="not_found")
    workspace = apply_actions(request.company_id, request.actions)
    return {"status": "applied", "workspace": workspace}


@app.get("/citadel/agent/models")
def citadel_agent_models() -> Dict[str, Any]:
    models = []
    for key in ("GROQ_MODEL", "CITADEL_AGENT_MODEL", "GROQ_MODEL1", "GROQ_MODEL2", "GROQ_MODEL3"):
        value = os.getenv(key, "").strip()
        if value:
            models.append(value)
    # Fallback defaults (no decommissioned models)
    defaults = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "qwen/qwen3-32b",
        "moonshotai/kimi-k2-instruct",
        "moonshotai/kimi-k2-instruct-0905",
        "openai/gpt-oss-20b",
    ]
    for model in defaults:
        if model not in models:
            models.append(model)
    return {"models": models}


@app.post("/shelves")
def shelves_create(request: ShelfCreateRequest) -> Dict[str, Any]:
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="name_required")
    return create_shelf(request.name.strip(), request.description, request.sort_order)


@app.get("/shelves")
def shelves_list() -> Dict[str, Any]:
    return {"shelves": list_shelves()}


@app.post("/shelves/{shelf_id}/items")
def shelves_add_item(shelf_id: str, request: ShelfItemRequest) -> Dict[str, Any]:
    return add_shelf_item(shelf_id, request.company_id, request.sort_order)


@app.get("/shelves/{shelf_id}/items")
def shelves_list_items(shelf_id: str) -> Dict[str, Any]:
    return {"items": list_shelf_items(shelf_id)}


@app.on_event("startup")
def start_citadel_refresh() -> None:
    def _runner() -> None:
        while True:
            try:
                _refresh_stale_companies(settings)
            except Exception:
                pass
            time.sleep(max(settings.citadel_refresh_interval_seconds, 3600))

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
