from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
import re
from uuid import uuid4

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from .config import Settings
from .db import (
    add_company_document,
    add_company_financial,
    add_company_ownership,
    add_company_person,
    add_company_subsidiary,
    get_company,
    get_company_profile,
    get_company_workspace,
    list_company_documents,
    list_company_financials,
    list_company_ownership,
    list_company_people,
    list_company_subsidiaries,
    upsert_company_workspace,
    update_company,
)
from .tools.web_tools import web_search, web_fetch, web_extract

AGENT_SYSTEM_PROMPT = (
    "You are the Citadel workspace agent. "
    "Return ONLY valid JSON with keys: summary (string) and actions (array). "
    "Each action must include a type and required fields. "
    "Allowed action types: add_node, update_node, remove_node, add_connection, remove_connection, "
    "update_company, add_person, add_document, add_ownership, add_subsidiary, add_financial. "
    "Node action schema: add_node {id?, node_type, x?, y?, data}. "
    "update_node {id, x?, y?, data?}. remove_node {id}. "
    "Example response: {\"summary\":\"Added a note\",\"actions\":[{\"type\":\"add_node\",\"node_type\":\"note\",\"data\":{\"text\":\"...\"}}]} "
    "Do not include markdown or extra text."
)


def generate_actions(
    settings: Settings,
    instruction: str,
    context: Dict[str, Any],
    model_override: Optional[str] = None,
    allow_web: bool = True,
) -> Dict[str, Any]:
    api_key = settings.groq_api_key
    model = model_override or os.getenv("CITADEL_AGENT_MODEL") or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    llm = ChatGroq(api_key=api_key, model=model, temperature=0.2)
    trimmed = _trim_context(context)
    if allow_web:
        web_results = _fetch_web_context(settings, context, instruction)
        if web_results:
            trimmed["web_results"] = web_results
    prompt = (
        "Instruction:\n"
        f"{instruction}\n\n"
        "Context JSON:\n"
        f"{json.dumps(trimmed, ensure_ascii=False, default=str)}\n\n"
        "Return JSON with summary and actions."
    )
    response = llm.invoke([SystemMessage(content=AGENT_SYSTEM_PROMPT), HumanMessage(content=prompt)])
    content = response.content if hasattr(response, "content") else str(response)
    parsed = _parse_actions(content)
    parsed["actions"] = normalize_actions(parsed.get("actions", []))
    return parsed


def apply_actions(company_id: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    workspace = get_company_workspace(company_id)
    workspace_data = workspace.get("data") if workspace else {"nodes": [], "connections": []}
    nodes = list(workspace_data.get("nodes") or [])
    connections = list(workspace_data.get("connections") or [])

    node_index = {node.get("id"): node for node in nodes if node.get("id")}
    connection_index = {conn.get("id"): conn for conn in connections if conn.get("id")}

    for action in actions:
        action_type = action.get("type")
        if action_type == "add_note":
            action_type = "add_node"
            action.setdefault("node_type", "note")
        elif action_type == "add_owner":
            action_type = "add_node"
            action.setdefault("node_type", "ownership")
        elif action_type == "add_person_node":
            action_type = "add_node"
            action.setdefault("node_type", "person")
        elif action_type == "add_document_node":
            action_type = "add_node"
            action.setdefault("node_type", "document")
        if action_type == "add_node":
            node_id = action.get("id") or str(uuid4())
            node = {
                "id": node_id,
                "type": action.get("node_type", action.get("type_name", action.get("kind", action.get("nodeType", "note")))),
                "x": float(action.get("x", 120)),
                "y": float(action.get("y", 120)),
                "data": action.get("data", {}),
            }
            nodes.append(node)
            node_index[node_id] = node
        elif action_type == "update_node":
            node_id = action.get("id")
            if not node_id or node_id not in node_index:
                continue
            node = node_index[node_id]
            if "x" in action:
                node["x"] = float(action["x"])
            if "y" in action:
                node["y"] = float(action["y"])
            if "data" in action:
                node["data"] = {**node.get("data", {}), **action.get("data", {})}
        elif action_type == "remove_node":
            node_id = action.get("id")
            if not node_id:
                continue
            nodes = [n for n in nodes if n.get("id") != node_id]
            node_index.pop(node_id, None)
            connections = [c for c in connections if c.get("from") != node_id and c.get("to") != node_id]
        elif action_type == "add_connection":
            conn_id = action.get("id") or str(uuid4())
            connection = {
                "id": conn_id,
                "from": action.get("from"),
                "to": action.get("to"),
                "label": action.get("label"),
            }
            if connection["from"] and connection["to"]:
                connections.append(connection)
                connection_index[conn_id] = connection
        elif action_type == "remove_connection":
            conn_id = action.get("id")
            if conn_id:
                connections = [c for c in connections if c.get("id") != conn_id]
            else:
                from_id = action.get("from")
                to_id = action.get("to")
                connections = [
                    c for c in connections if not (c.get("from") == from_id and c.get("to") == to_id)
                ]
        elif action_type == "update_company":
            update_company(
                company_id,
                name=action.get("name"),
                description=action.get("description"),
                sector=action.get("sector"),
                industry=action.get("industry"),
                country=action.get("country"),
                website=action.get("website"),
            )
        elif action_type == "add_person":
            add_company_person(
                company_id=company_id,
                name=action.get("name", ""),
                role=action.get("role"),
                start_date=action.get("start_date"),
                end_date=action.get("end_date"),
                bio=action.get("bio"),
                source=action.get("source"),
            )
        elif action_type == "add_document":
            add_company_document(
                company_id=company_id,
                doc_type=action.get("doc_type"),
                title=action.get("title"),
                url=action.get("url"),
                content=action.get("content"),
                source=action.get("source"),
                published_at=action.get("published_at"),
            )
        elif action_type == "add_subsidiary":
            add_company_subsidiary(
                company_id=company_id,
                name=action.get("name", ""),
                country=action.get("country"),
                ownership_pct=action.get("ownership_pct"),
                source=action.get("source"),
            )
        elif action_type == "add_ownership":
            add_company_ownership(
                company_id=company_id,
                holder_name=action.get("holder_name", ""),
                holder_type=action.get("holder_type"),
                percent=_parse_number(action.get("percent")),
                shares=_parse_number(action.get("shares")),
                as_of_date=action.get("as_of_date"),
                source=action.get("source"),
            )
        elif action_type == "add_financial":
            add_company_financial(
                company_id=company_id,
                metric=action.get("metric", ""),
                value=_parse_number(action.get("value")),
                period_start=action.get("period_start"),
                period_end=action.get("period_end"),
                unit=action.get("unit"),
                currency=action.get("currency"),
                source=action.get("source"),
            )

    workspace_payload = {"nodes": nodes, "connections": connections}
    upsert_company_workspace(company_id, workspace_payload)
    return workspace_payload


def build_context(company_id: str) -> Dict[str, Any]:
    company = get_company(company_id) or {}
    profile = get_company_profile(company_id) or {}
    people = list_company_people(company_id)
    documents = list_company_documents(company_id, limit=20)
    ownership = list_company_ownership(company_id, limit=20)
    subsidiaries = list_company_subsidiaries(company_id)
    financials = list_company_financials(company_id, limit=50)
    workspace = get_company_workspace(company_id) or {"data": {"nodes": [], "connections": []}}
    return {
        "company": company,
        "profile": profile,
        "people": people,
        "documents": documents,
        "ownership": ownership,
        "subsidiaries": subsidiaries,
        "financials": financials,
        "workspace": workspace.get("data", {}),
    }


def _trim_context(context: Dict[str, Any]) -> Dict[str, Any]:
    trimmed = dict(context)
    workspace = trimmed.get("workspace") or {}
    nodes = workspace.get("nodes") or []
    connections = workspace.get("connections") or []
    workspace["nodes"] = nodes[:30]
    workspace["connections"] = connections[:50]
    trimmed["workspace"] = workspace
    trimmed["documents"] = (trimmed.get("documents") or [])[:10]
    trimmed["ownership"] = (trimmed.get("ownership") or [])[:10]
    trimmed["financials"] = (trimmed.get("financials") or [])[:20]
    trimmed["people"] = (trimmed.get("people") or [])[:10]
    trimmed["subsidiaries"] = (trimmed.get("subsidiaries") or [])[:20]
    return trimmed


def _fetch_web_context(
    settings: Settings,
    context: Dict[str, Any],
    instruction: str,
) -> List[Dict[str, Any]]:
    company = context.get("company") or {}
    name = company.get("name") or ""
    query = f"{name} {instruction}".strip()
    if not query:
        return []
    results = web_search(settings, query, max_results=5)
    trimmed: List[Dict[str, Any]] = []
    for item in results[:3]:
        trimmed.append(
            {
                "title": item.get("title"),
                "url": item.get("href"),
                "snippet": item.get("body"),
            }
        )

    # Fetch and extract top URLs for richer context
    pages: List[Dict[str, Any]] = []
    for item in results[:2]:
        url = item.get("href")
        if not url:
            continue
        try:
            fetched = web_fetch(settings, url)
            extracted = web_extract(settings, fetched.get("text", ""))
            pages.append(
                {
                    "title": item.get("title"),
                    "url": url,
                    "excerpt": extracted.get("text", "")[:2000],
                }
            )
        except Exception:
            continue
    if pages:
        trimmed.append({"pages": pages})
    return trimmed


def _parse_actions(content: str) -> Dict[str, Any]:
    parsed = None
    try:
        parsed = json.loads(content)
    except Exception:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
            except Exception:
                parsed = None
    if parsed is None:
        return {"summary": "No valid actions produced.", "actions": []}
    if not isinstance(parsed, dict):
        return {"summary": "No valid actions produced.", "actions": []}
    actions = parsed.get("actions", [])
    if not isinstance(actions, list):
        actions = []
    return {"summary": parsed.get("summary", ""), "actions": actions}


def normalize_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        action_type = action.get("type")
        if not action_type and action.get("action"):
            action_type = action.get("action")
            action["type"] = action_type
        if action_type in {"add_note", "add_owner", "add_person_node", "add_document_node"}:
            normalized.append(action)
            continue
        if action_type == "add_node":
            if "node_type" not in action and "nodeType" in action:
                action["node_type"] = action.get("nodeType")
            normalized.append(action)
            continue
        normalized.append(action)
    return normalized


def _parse_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    multiplier = 1.0
    suffix = text[-1].upper()
    if suffix in {"K", "M", "B", "T"}:
        text = text[:-1]
        multiplier = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}[suffix]
    try:
        return float(text) * multiplier
    except ValueError:
        return None
