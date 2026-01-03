from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from langchain_groq import ChatGroq
from pydantic import BaseModel, create_model

from .config import Settings
from .db import memory_put, memory_search
from .tool_registry import TOOLS
from .tool_dispatch import dispatch_tool
from .tools.web_tools import web_extract, web_fetch_browser


SYSTEM_PROMPT = (
    "You are a finance analysis assistant. Use tools to fetch data. "
    "Include URLs in responses when using sources. "
    "Be concise and show calculations when relevant."
)

NEPSE_SYSTEM_PROMPT = (
    "You are a NEPSE market analyst. Use NEPSE tools for factual data and calculations. "
    "Do not make up numbers. If data is missing, say so. "
    "Avoid investment advice; use neutral language like 'could' or 'may'. "
    "Provide sources when possible. "
    "Keep responses concise: 5-8 bullets max, each 1 line. "
    "Only include data relevant to the question; omit boilerplate. "
    "Prefer symbol-specific tools (nepse.symbol_snapshot, nepse.company_details, nepse.price_volume_history). "
    "Avoid large list tools unless explicitly requested. "
    "Never include example outputs or fabricated sample IDs. "
    "Never claim to have executed or created a proposal unless a tool call succeeded. "
    "Do not show pseudo tool calls or 'expected output' blocks. "
    "Do not tell the user to 'use' a tool; call tools yourself when needed. "
    "If asked to recommend a stock without a symbol, call nepse.top_gainers and nepse.top_turnover_scrips, "
    "pick a single candidate with liquidity, and explain why in 2 bullets. "
    "If a trade is requested: "
    "1) call paper.portfolios and list portfolio id+name from real tool output, "
    "2) if none exist, call paper.portfolio_create (name: 'Global Portfolio', starting_cash: 100000, currency: NPR), "
    "3) fetch symbol data with tools, summarize rationale+risks, "
    "4) propose trade with paper.trade_propose using the real portfolio_id. "
    "If any required data is missing, stop and ask the user to confirm or provide it."
)

_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
_MAX_HISTORY_MESSAGES = 20
_MAX_HISTORY_CHARS = 12000
_MAX_LINKS = 2
_MAX_LINK_CHARS = 1500
_MAX_MESSAGE_FOR_LINKS = 2000
_MAX_REQUEST_CHARS = 8000
_MAX_MEMORY_CHARS = 2000


def _json_type_to_py(json_type: str) -> Any:
    if json_type == "string":
        return str
    if json_type == "integer":
        return int
    if json_type == "number":
        return float
    if json_type == "boolean":
        return bool
    if json_type == "array":
        return list
    if json_type == "object":
        return dict
    return str


def _build_args_schema(input_schema: Dict[str, Any], model_name: str) -> type[BaseModel]:
    properties = input_schema.get("properties", {})
    required = set(input_schema.get("required", []))
    fields: Dict[str, Tuple[Any, Any]] = {}
    for name, spec in properties.items():
        py_type = _json_type_to_py(spec.get("type", "string"))
        if name in required:
            fields[name] = (py_type, ...)
        else:
            fields[name] = (Optional[py_type], None)
    return create_model(model_name, **fields)


def _build_tools(settings: Settings) -> List[StructuredTool]:
    return _build_tools_filtered(settings, None)


def _build_tools_filtered(settings: Settings, tool_names: List[str] | None) -> List[StructuredTool]:
    tools: List[StructuredTool] = []
    for tool in TOOLS:
        if tool_names is not None and tool.name not in tool_names:
            continue
        model_name = f"ToolArgs_{tool.name.replace('.', '_')}"
        args_schema = _build_args_schema(tool.input_schema, model_name)

        def _call_tool(_tool_name: str = tool.name, **kwargs: Any) -> Any:
            return dispatch_tool(settings, _tool_name, kwargs)

        tools.append(
            StructuredTool.from_function(
                name=tool.name,
                description=tool.description,
                args_schema=args_schema,
                func=_call_tool,
            )
        )
    return tools


def _build_executor(settings: Settings) -> AgentExecutor:
    load_dotenv()
    api_key = settings.groq_api_key.strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing")
    model = settings.groq_model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    llm = ChatGroq(api_key=api_key, model=model, temperature=settings.groq_temperature)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    tools = _build_tools(settings)
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False)


def _build_executor_custom(
    settings: Settings,
    tool_names: List[str],
    system_prompt: str,
    model_override: str | None = None,
) -> AgentExecutor:
    load_dotenv()
    api_key = settings.groq_api_key.strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing")
    model = model_override or settings.groq_model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    llm = ChatGroq(api_key=api_key, model=model, temperature=settings.groq_temperature)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    tools = _build_tools_filtered(settings, tool_names)
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False)


def _to_messages(history: List[Dict[str, str]]) -> List[Any]:
    messages: List[Any] = []
    for item in history:
        role = item.get("role")
        content = item.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


def _extract_urls(text: str, max_links: int = _MAX_LINKS) -> List[str]:
    matches = _URL_PATTERN.findall(text or "")
    cleaned: List[str] = []
    for item in matches:
        url = item.rstrip(").,;\"'[]<>")
        if url and url not in cleaned:
            cleaned.append(url)
        if len(cleaned) >= max_links:
            break
    return cleaned


def _build_link_context(settings: Settings, message: str) -> List[SystemMessage]:
    if len(message or "") > _MAX_MESSAGE_FOR_LINKS:
        return []
    urls = _extract_urls(message)
    if not urls:
        return []
    entries: List[str] = []
    for url in urls:
        try:
            fetched = web_fetch_browser(settings, url)
            extracted = web_extract(settings, fetched.get("text", ""))
            text = extracted.get("text", "")
            if not text:
                continue
            entries.append(f"Source: {fetched.get('url')}\n{text[:_MAX_LINK_CHARS]}")
        except Exception:
            continue
    if not entries:
        return []
    return [SystemMessage(content="Linked content:\n" + "\n\n".join(entries))]


def _trim_history(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if not history:
        return []
    trimmed = history[-_MAX_HISTORY_MESSAGES:]
    total_chars = 0
    kept: List[Dict[str, str]] = []
    for item in reversed(trimmed):
        content = item.get("content", "") or ""
        size = len(content)
        if total_chars + size > _MAX_HISTORY_CHARS:
            break
        kept.append(item)
        total_chars += size
    return list(reversed(kept))


def _trim_messages_by_chars(messages: List[Any], max_chars: int) -> List[Any]:
    if not messages:
        return []
    total = 0
    kept: List[Any] = []
    for msg in reversed(messages):
        content = getattr(msg, "content", "") or ""
        size = len(content)
        if total + size > max_chars:
            break
        kept.append(msg)
        total += size
    return list(reversed(kept))


def chat_with_tools(
    message: str,
    history: List[Dict[str, str]],
    use_memory: bool,
    store_memory: bool,
    settings: Settings,
    conversation_id: str | None = None,
    explore_links: bool = True,
) -> str:
    memory_context = ""
    if use_memory:
        items = memory_search(
            message,
            limit=5,
            conversation_id=conversation_id,
        )
        if items:
            memory_context = "\n".join(item.get("content", "") for item in items if item)
        # keep memory context bounded to avoid exceeding model input limits
        if len(memory_context) > _MAX_MEMORY_CHARS:
            memory_context = "..." + memory_context[-_MAX_MEMORY_CHARS:]

    history_messages = _to_messages(_trim_history(history))
    if explore_links:
        history_messages = _build_link_context(settings, message) + history_messages
    if memory_context:
        history_messages = [SystemMessage(content=f"Memory context:\n{memory_context}")] + history_messages

    # Ensure the overall request (concatenated messages) is not too large
    history_messages = _trim_messages_by_chars(history_messages, _MAX_REQUEST_CHARS)

    executor = _build_executor(settings)
    result = executor.invoke(
        {"input": message, "chat_history": history_messages}
    )
    reply = result.get("output", "")
    if store_memory:
        if message:
            memory_put(message, ["user"], conversation_id=conversation_id)
        if reply:
            memory_put(reply, ["assistant"], conversation_id=conversation_id)
    return reply


def chat_with_tools_custom(
    message: str,
    history: List[Dict[str, str]],
    settings: Settings,
    tool_names: List[str],
    system_prompt: str,
    model_override: str | None = None,
    use_memory: bool = False,
    store_memory: bool = False,
    conversation_id: str | None = None,
    explore_links: bool = False,
) -> str:
    memory_context = ""
    if use_memory:
        items = memory_search(
            message,
            limit=5,
            conversation_id=conversation_id,
        )
        if items:
            memory_context = "\n".join(item.get("content", "") for item in items if item)
        if len(memory_context) > _MAX_MEMORY_CHARS:
            memory_context = "..." + memory_context[-_MAX_MEMORY_CHARS:]

    history_messages = _to_messages(_trim_history(history))
    if explore_links:
        history_messages = _build_link_context(settings, message) + history_messages
    if memory_context:
        history_messages = [SystemMessage(content=f"Memory context:\n{memory_context}")] + history_messages

    history_messages = _trim_messages_by_chars(history_messages, _MAX_REQUEST_CHARS)

    executor = _build_executor_custom(
        settings,
        tool_names=tool_names,
        system_prompt=system_prompt,
        model_override=model_override,
    )
    result = executor.invoke(
        {"input": message, "chat_history": history_messages}
    )
    reply = result.get("output", "")
    if store_memory:
        if message:
            memory_put(message, ["user"], conversation_id=conversation_id)
        if reply:
            memory_put(reply, ["assistant"], conversation_id=conversation_id)
    return reply
