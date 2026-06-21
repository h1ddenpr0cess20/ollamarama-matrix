from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Iterable, List

import logging
import shlex

from fastmcp import Client
import mcp.types


logger = logging.getLogger(__name__)


class FastMCPClient:
    """Adapter around ``fastmcp`` for listing and calling MCP server tools.

    Normalizes a variety of server spec formats (URL strings, shell strings,
    argv lists, and dicts) into fastmcp client configs, and bridges fastmcp's
    async API into synchronous calls usable from the rest of the app.
    """

    def __init__(self, servers: Dict[str, Any]) -> None:
        """Normalize and store MCP server specifications.

        Args:
            servers: Mapping of server name to spec (URL string, shell string,
                argv list, or config dict).
        """
        self._servers: Dict[str, Any] = {}
        logger.debug("FastMCPClient init with servers: %s", list(servers.keys()))
        for name, spec in servers.items():
            if spec is None:
                continue
            if isinstance(spec, (list, tuple)):
                parts = list(spec)
                if not parts:
                    continue
                cfg: Dict[str, Any] = {"command": str(parts[0])}
                if len(parts) > 1:
                    cfg["args"] = [str(a) for a in parts[1:]]
                self._servers[name] = cfg
                logger.debug("Normalized server '%s' from list: %s", name, cfg)
                continue
            if isinstance(spec, str):
                target = spec.strip()
                if not target:
                    continue
                if "://" in target:
                    self._servers[name] = target
                    logger.debug("Using server '%s' URL: %s", name, target)
                else:
                    parts = shlex.split(target)
                    cfg: Dict[str, Any] = {"command": parts[0]}
                    if len(parts) > 1:
                        cfg["args"] = parts[1:]
                    self._servers[name] = cfg
                    logger.debug("Normalized server '%s' from string to command+args: %s", name, cfg)
                continue
            if isinstance(spec, dict):
                cfg = dict(spec)
                cmd = cfg.get("command")
                if isinstance(cmd, str) and ("args" not in cfg or isinstance(cfg.get("args"), str)) and " " in cmd:
                    parts = shlex.split(cmd)
                    cfg["command"] = parts[0]
                    if len(parts) > 1:
                        cfg["args"] = parts[1:]
                if isinstance(cfg.get("args"), str):
                    cfg["args"] = shlex.split(cfg["args"])  # type: ignore[index]
                if "url" in cfg and "target" not in cfg:
                    cfg["target"] = cfg["url"]
                self._servers[name] = cfg
                logger.debug("Server '%s' config: %s", name, cfg)
                continue
        self._tool_servers: Dict[str, str] = {}

        for name, spec in list(self._servers.items()):
            if isinstance(spec, str) and "://" in spec:
                continue
            if isinstance(spec, dict):
                cmd = spec.get("command")
                args = spec.get("args", [])
                if isinstance(cmd, str):
                    argv = [cmd] + ([str(a) for a in args] if isinstance(args, (list, tuple)) else [])
                    cmdline = " ".join(shlex.quote(p) for p in argv)
                    wrapped = {
                        "command": "bash",
                        "args": ["-lc", f"{cmdline} 2>/dev/null"],
                    }
                    self._servers[name] = wrapped
                    logger.debug("Wrapped server '%s' command for silent output", name)

    def _iter_transports(self, transport: Any) -> Iterable[Any]:
        """Yield transport objects, including composite underlying transports."""
        stack = [transport]
        seen: set[int] = set()
        while stack:
            current = stack.pop()
            if current is None:
                continue
            ident = id(current)
            if ident in seen:
                continue
            seen.add(ident)
            yield current
            underlying = getattr(current, "_underlying_transports", None)
            if isinstance(underlying, list):
                stack.extend(underlying)

    def _configure_transport(self, transport: Any) -> None:
        """Tune transports for short-lived MCP sessions."""
        for current in self._iter_transports(transport):
            if hasattr(current, "keep_alive"):
                try:
                    current.keep_alive = False
                except Exception:
                    pass

    def _mark_transport_stopped(self, transport: Any) -> None:
        """Preempt transport __del__ loop errors by setting stop events."""
        for current in self._iter_transports(transport):
            stop_event = getattr(current, "_stop_event", None)
            if stop_event is None:
                continue
            try:
                stop_event.set()
            except Exception:
                pass

    async def _list_tools_async(self) -> List[Dict[str, Any]]:
        """Connect to each configured server and collect tool schemas.

        Offline or misconfigured servers are logged and skipped.

        Returns:
            A list of OpenAI-style function tool definitions.
        """
        schema: List[Dict[str, Any]] = []
        for name, cfg in self._servers.items():
            logger.debug("Listing tools from MCP server '%s'", name)
            spec = cfg
            client = Client({name: spec})
            self._configure_transport(client.transport)
            try:
                async with client:
                    tools = await client.list_tools()
                logger.debug("Server '%s' returned %d tool(s)", name, len(tools))
            except Exception as e:
                logger.error("Failed to list tools from MCP server '%s': %s", name, e)
                continue
            finally:
                self._mark_transport_stopped(client.transport)
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
        """Run a coroutine to completion from synchronous code.

        Uses ``asyncio.run`` when no loop is running; otherwise runs the
        coroutine on a fresh loop in a dedicated thread so it does not clash
        with an already-running event loop.

        Args:
            coro: The coroutine to execute.

        Returns:
            The coroutine's result.

        Raises:
            Exception: Re-raises any exception raised by the coroutine.
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            logger.debug("No running loop; executing coroutine with asyncio.run")
            return asyncio.run(coro)
        result: Dict[str, Any] = {}

        def runner() -> None:
            """Run the coroutine on a new event loop in this thread."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result["value"] = loop.run_until_complete(coro)
            except Exception as e:
                result["exc"] = e
            finally:
                loop.close()

        import threading

        t = threading.Thread(target=runner)
        t.start()
        t.join()
        if "exc" in result:
            raise result["exc"]  # type: ignore[misc]
        return result.get("value")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return tool schemas from all configured MCP servers (synchronous)."""
        return self._run(self._list_tools_async())

    async def _call_tool_async(self, client: Client, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on a server and normalize its result.

        Args:
            client: The fastmcp client connected to the target server.
            name: The tool name to call.
            arguments: Arguments to pass to the tool.

        Returns:
            The tool's structured data, structured content, or aggregated
            text wrapped as ``{"result": str}``.
        """
        logger.debug("Calling MCP tool '%s' on client", name)
        self._configure_transport(client.transport)
        try:
            async with client:
                result = await client.call_tool(name, arguments)
        finally:
            self._mark_transport_stopped(client.transport)
        if result.data is not None:
            logger.debug("Tool '%s' returned 'data' field", name)
            return result.data
        if result.structured_content is not None:
            logger.debug("Tool '%s' returned 'structured_content' field", name)
            return result.structured_content
        texts: List[str] = []
        for block in result.content:
            if isinstance(block, mcp.types.TextContent):
                texts.append(block.text)
        aggregated = "\n".join(texts)
        logger.debug("Tool '%s' returned %d text block(s)", name, len(texts))
        return {"result": aggregated}

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Call an MCP tool by name and return a JSON string result.

        Args:
            name: The tool name (resolved to its owning server).
            arguments: Arguments to pass to the tool.

        Returns:
            A JSON string with the tool result, or a JSON error object if the
            tool is unknown or execution fails.
        """
        server_name = self._tool_servers.get(name)
        if server_name is None:
            logger.warning("Attempted to call unknown MCP tool '%s'", name)
            return json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)
        cfg = self._servers.get(server_name)
        client = Client({server_name: cfg})
        try:
            logger.debug("Dispatching tool '%s' to server '%s' with args: %s", name, server_name, arguments)
            data = self._run(self._call_tool_async(client, name, arguments))
        except Exception as e:
            logger.exception("Error executing MCP tool '%s' on server '%s'", name, server_name)
            return json.dumps({"error": f"Tool execution error for {name}: {e}"}, ensure_ascii=False)
        try:
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            logger.debug("Non-JSON-serializable tool result for '%s'; stringifying", name)
            return json.dumps({"result": str(data)}, ensure_ascii=False)


__all__ = ["FastMCPClient"]
