from __future__ import annotations

import os
from typing import Any, Dict, List

import requests


class MCPClient:
    def __init__(self, base_url: str | None = None, timeout: int = 30) -> None:
        self.base_url = base_url or os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000")
        self.timeout = timeout

    def list_tools(self) -> List[Dict[str, Any]]:
        response = requests.get(f"{self.base_url}/tools", timeout=self.timeout)
        response.raise_for_status()
        return response.json().get("tools", [])

    def invoke(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/invoke",
            json={"name": name, "arguments": arguments},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
