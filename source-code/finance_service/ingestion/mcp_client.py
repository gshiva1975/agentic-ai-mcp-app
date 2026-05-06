# finance_service/ingestion/mcp_client.py

import uuid
import requests


class MCPClient:
    def __init__(self, url: str, timeout: int = 5):
        self.url     = url
        self.timeout = timeout

    def call_tool(self, tool_name: str, arguments: dict | None = None) -> list:
        payload = {
            "jsonrpc": "2.0",
            "method":  "tools/call",
            "params":  {
                "name":      tool_name,
                "arguments": arguments or {},
            },
            "id": str(uuid.uuid4()),
        }

        try:
            response = requests.post(self.url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise RuntimeError(f"MCP Error: {data['error']}")

            return data.get("result", [])

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"MCP request failed: {e}")
