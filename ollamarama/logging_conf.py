import logging
import logging.config
import re


class MatrixHighlighter:
    """Custom highlighter for Matrix-related text in logs.

    - Highlights Matrix user IDs (e.g., @user:server) in bold cyan
    - Highlights room IDs / aliases (e.g., !room:server, #room:server) in magenta
    - Highlights message payloads in white (between "sent" and "in")
    - Highlights model names after "Model set to" in bold yellow
    - Highlights verified device IDs in green
    - Highlights file paths after "Persisted device_id to" in green
    """

    _user_re = re.compile(r"@[A-Za-z0-9_.\-:]+\b")
    _room_re = re.compile(r"[#!][^\s:]+:[A-Za-z0-9_.\-]+")
    _model_re = re.compile(r"\bModel set to\s+(?P<model>\S+)")
    _sent_msg_re = re.compile(r"\bsent\s+(?P<msg>.+?)\s+in\s+")
    _joined_re = re.compile(r"^(?P<bot>.+?)\s+joined\s+(?P<room>\S+)")
    _sent_line_re = re.compile(r"^(?P<display>.+?)\s+\((?P<id>@[^)]+)\)\s+sent\s+(?P<msg>.+?)\s+in\s+(?P<room>\S+)", re.S)
    _sending_resp_re = re.compile(r"Sending response to\s+(?P<name>.+?)\s+in\s+(?P<room>\S+):\s+(?P<body>.*)", re.S)
    _thinking_re = re.compile(r"Model thinking for\s+(?P<who>.+?):\s+(?P<thinking>.*)", re.S)
    _sys_prompt_re = re.compile(r"System prompt for\s+(?P<who>.+?)\s+\(.*?\)\s+set to\s+'(?P<prompt>.*)'")
    _verified_re = re.compile(r"\bverified device\s+(?P<dev>\S+)")
    _persist_re = re.compile(r"\bPersisted device_id to\s+(?P<path>\S+)")
    # Tool-call lines: "Tool (MCP|builtin): <name> args=<json>"
    _tool_call_re = re.compile(r"(?P<tool>Tool)\s+\((?P<origin>MCP|builtin)\):\s+(?P<name>\S+)\s+args=(?P<args>.*)")

    def __call__(self, value):
        """Make the highlighter callable like Rich's Highlighter.

        Accepts either a string or a `rich.text.Text`, applies styles in place,
        and returns a `Text` instance.

        Args:
            value: Text content to highlight.

        Returns:
            A `Text` object with styles applied (or the original value if Rich
            is unavailable).
        """
        try:
            from rich.text import Text  # type: ignore
        except Exception:  # pragma: no cover - only used when rich is present
            return value
        text = value if hasattr(value, "stylize") else Text(str(value))
        self.highlight(text)
        return text

    def highlight(self, text) -> None:  # rich.text.Text-like interface
        """Apply highlighting to a Rich `Text` object in place.

        Args:
            text: A `rich.text.Text`-like object to stylize.

        Returns:
            None. Modifies `text` in place.
        """
        s = text.plain

        for m in self._user_re.finditer(s):
            text.stylize("bold cyan", m.start(), m.end())

        for m in self._room_re.finditer(s):
            text.stylize("magenta", m.start(), m.end())

        for m in self._model_re.finditer(s):
            span = m.span("model")
            text.stylize("bold yellow", span[0], span[1])

        for m in self._sent_msg_re.finditer(s):
            span = m.span("msg")
            text.stylize("white", span[0], span[1])

        # Sender line with display name and id
        for m in self._sent_line_re.finditer(s):
            dspan = m.span("display")
            rsp = m.span("room")
            text.stylize("bold cyan", dspan[0], dspan[1])
            text.stylize("magenta", rsp[0], rsp[1])

        # Bot joined room: color bot display name and room id
        for m in self._joined_re.finditer(s):
            bspan = m.span("bot")
            rsp = m.span("room")
            text.stylize("bold cyan", bspan[0], bspan[1])
            text.stylize("magenta", rsp[0], rsp[1])

        # Sending response: color recipient name; bold only the response text (after first newline)
        for m in self._sending_resp_re.finditer(s):
            nspan = m.span("name")
            text.stylize("bold cyan", nspan[0], nspan[1])
            bsp = m.span("body")
            body_text = s[bsp[0]:bsp[1]]
            nl = body_text.find("\n")
            if nl >= 0:
                # Only bold the response payload after the header line
                text.stylize("bold", bsp[0] + nl + 1, bsp[1])
            else:
                text.stylize("bold", bsp[0], bsp[1])

        # Thinking lines: color who and dim italicize the thinking content
        for m in self._thinking_re.finditer(s):
            wsp = m.span("who")
            tsp = m.span("thinking")
            text.stylize("bold cyan", wsp[0], wsp[1])
            text.stylize("dim italic", tsp[0], tsp[1])

        # System prompt changes: color who for visibility
        for m in self._sys_prompt_re.finditer(s):
            wsp = m.span("who")
            text.stylize("bold cyan", wsp[0], wsp[1])

        for m in self._verified_re.finditer(s):
            span = m.span("dev")
            text.stylize("green", span[0], span[1])

        for m in self._persist_re.finditer(s):
            span = m.span("path")
            text.stylize("green", span[0], span[1])

        # Tool-call coloring
        for m in self._tool_call_re.finditer(s):
            tsp = m.span("tool")
            osp = m.span("origin")
            nsp = m.span("name")
            asp = m.span("args")
            text.stylize("bold cyan", tsp[0], tsp[1])
            text.stylize("cyan", osp[0], osp[1])
            text.stylize("bold yellow", nsp[0], nsp[1])
            text.stylize("dim", asp[0], asp[1])


def setup_logging(level: str = "INFO", json: bool = False) -> None:
    """Configure logging using Rich for colorful, structured output.

    Falls back to standard logging if Rich is unavailable. The ``json`` flag is
    retained for backward compatibility but is treated as a request for a more
    detailed format; it does not emit strict JSON.

    Args:
        level: Logging level name (e.g., ``"INFO"`` or ``"DEBUG"``).
        json: If True, include the logger name in the plain fallback format.

    Returns:
        None.
    """
    lvl = getattr(logging, level.upper(), logging.INFO)

    # Silence any previously configured handlers, mirroring prior behavior
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": True,
    })

    try:
        # Prefer Rich if installed
        from rich.console import Console
        from rich.logging import RichHandler
        from rich.traceback import install as rich_traceback_install

        # Better tracebacks in the console
        rich_traceback_install(show_locals=False)

        # Disable generic syntax highlighting; we apply targeted styles via a custom highlighter
        console = Console(highlight=False)
        highlighter = MatrixHighlighter()
        handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            markup=True,
            show_level=True,
            show_time=True,
            show_path=False,
            highlighter=highlighter,
        )
        # Use message-only format; Rich renders time/level
        datefmt = "[%X]"
        fmt = "%(message)s"
        if json:
            fmt = "%(name)s - %(message)s"

        # Route only our package logs to the handler; silence others at root
        root = logging.getLogger()
        root.handlers = []
        root.setLevel(logging.ERROR)

        pkg_logger = logging.getLogger("ollamarama")
        pkg_logger.handlers = []
        pkg_logger.setLevel(lvl)
        # Manually build a Formatter for non-Rich fallback of message formatting inside RichHandler
        # RichHandler ignores the formatter for message, but keeps datefmt for legacy; safe to set basicConfig-like state
        logging.Formatter(fmt=fmt, datefmt=datefmt)
        pkg_logger.addHandler(handler)
        pkg_logger.propagate = False
    except Exception:
        # Fallback to plain logging
        fmt = (
            "%(asctime)s %(levelname)s %(name)s %(message)s"
            if json
            else "%(asctime)s - %(levelname)s - %(message)s"
        )
        root = logging.getLogger()
        root.handlers = []
        root.setLevel(logging.ERROR)
        pkg_logger = logging.getLogger("ollamarama")
        pkg_logger.handlers = []
        pkg_logger.setLevel(lvl)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt))
        pkg_logger.addHandler(handler)
        pkg_logger.propagate = False
