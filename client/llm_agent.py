from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from langchain_groq import ChatGroq
from pydantic import BaseModel, create_model

from .mcp_client import MCPClient


SYSTEM_PROMPT = (
    "You are a finance analysis assistant. Use tools to fetch data. "
    "When you use sources, include the URL in your response. "
    "Be concise and show calculations when relevant. "
    "Prefer plain text paragraphs. Avoid heavy markdown and avoid using asterisks for lists. "
    "If a list is needed, keep it short and use simple numbering."
)


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


class LLMClient:
    def __init__(self) -> None:
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing")
        self.mcp = MCPClient()
        self.tools = self._load_tools()
        model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
        self.llm = ChatGroq(api_key=api_key, model=model, temperature=0.2)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        self.executor = AgentExecutor(agent=agent, tools=self.tools, verbose=False)

    def _load_tools(self) -> List[StructuredTool]:
        tools = []
        for tool in self.mcp.list_tools():
            name = tool.get("name")
            description = tool.get("description", "")
            input_schema = tool.get("input_schema", {"type": "object", "properties": {}})
            model_name = f"ToolArgs_{name.replace('.', '_')}"
            args_schema = _build_args_schema(input_schema, model_name)

            def _call_tool(_tool_name: str = name, **kwargs: Any) -> Any:
                result = self.mcp.invoke(_tool_name, kwargs)
                return result.get("result", {})

            tools.append(
                StructuredTool.from_function(
                    name=name, description=description, args_schema=args_schema, func=_call_tool
                )
            )
        return tools

    def ask(
        self,
        user_input: str,
        chat_history: List[Any],
        memory_context: str = "",
    ) -> str:
        combined_input = user_input
        if memory_context:
            combined_input = f"Memory context:\n{memory_context}\n\nUser:\n{user_input}"
        response = self.executor.invoke(
            {"input": combined_input, "chat_history": chat_history}
        )
        return response.get("output", "")

    @staticmethod
    def to_messages(history: List[Dict[str, str]]) -> List[Any]:
        messages: List[Any] = []
        for item in history:
            role = item.get("role")
            content = item.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        return messages
