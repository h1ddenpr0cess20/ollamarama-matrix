from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

from fastmcp import Client
import mcp.types


class FastMCPClient:
    def __init__(self, servers: Dict[str, Any]) -> None:
        self._servers: Dict[str, Any] = {}
        for name, spec in servers.items():
            if isinstance(spec, str):
                target = spec.strip()
                if not target:
                    continue
                if "://" not in target and " " in target:
                    import shlex

                    parts = shlex.split(target)
                    cfg: Dict[str, Any] = {"command": parts[0]}
                    if len(parts) > 1:
                        cfg["args"] = parts[1:]
                    self._servers[name] = cfg
                else:
                    self._servers[name] = target
            elif isinstance(spec, dict):
                cfg = dict(spec)
                cmd = cfg.get("command")
                if isinstance(cmd, str) and "args" not in cfg and " " in cmd:
                    import shlex

                    parts = shlex.split(cmd)
                    cfg["command"] = parts[0]
                    if len(parts) > 1:
                        cfg["args"] = parts[1:]
                self._servers[name] = cfg
        self._tool_servers: Dict[str, str] = {}

    async def _list_tools_async(self) -> List[Dict[str, Any]]:
        schema: List[Dict[str, Any]] = []
        for name, cfg in self._servers.items():
            client = Client(cfg) if isinstance(cfg, str) else Client({name: cfg})
            async with client:
                tools = await client.list_tools()
            for tool in tools:
                self._tool_servers[tool.name] = name
                schema.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": tool.inputSchema
                            or {
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False,
                            },
                        },
                    }
                )
        return schema

    def _run(self, coro):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        result: Dict[str, Any] = {}

        def runner() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result["value"] = loop.run_until_complete(coro)
            finally:
                loop.close()

        import threading

        t = threading.Thread(target=runner)
        t.start()
        t.join()
        return result.get("value")

    def list_tools(self) -> List[Dict[str, Any]]:
        return self._run(self._list_tools_async())

    async def _call_tool_async(self, client: Client, name: str, arguments: Dict[str, Any]) -> Any:
        async with client:
            result = await client.call_tool(name, arguments)
        if result.data is not None:
            return result.data
        if result.structured_content is not None:
            return result.structured_content
        texts: List[str] = []
        for block in result.content:
            if isinstance(block, mcp.types.TextContent):
                texts.append(block.text)
        return {"result": "\n".join(texts)}

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        server_name = self._tool_servers.get(name)
        if server_name is None:
            return json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)
        cfg = self._servers.get(server_name)
        client = Client(cfg) if isinstance(cfg, str) else Client({server_name: cfg})
        try:
            data = self._run(self._call_tool_async(client, name, arguments))
        except Exception as e:
            return json.dumps({"error": f"Tool execution error for {name}: {e}"}, ensure_ascii=False)
        try:
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return json.dumps({"result": str(data)}, ensure_ascii=False)


__all__ = ["FastMCPClient"]
