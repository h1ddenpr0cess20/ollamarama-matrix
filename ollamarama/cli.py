import argparse
import json
import logging
import os
import runpy
import sys
from typing import List, Optional

from .logging_conf import setup_logging
import asyncio
from .config import load_config, validate_config, summarize
from .app import run as run_app


def build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line argument parser.

    Returns:
        Configured `argparse.ArgumentParser` for the Ollamarama CLI.
    """
    parser = argparse.ArgumentParser(
        prog="ollamarama-matrix",
        description=(
            "Ollamarama Matrix bot. Modern CLI that validates config and runs the app."
        ),
        add_help=True,
    )
    parser.add_argument(
        "-L",
        "--log-level",
        default=os.getenv("OLLAMARAMA_LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level for the launcher.",
    )
    # Common flags for configuration and runtime overrides.
    parser.add_argument("-c", "--config", help="Path to config.json (default: ./config.json)")
    parser.add_argument("-E", "--e2e", action="store_true", help="Enable end-to-end encryption (overrides config)")
    parser.add_argument("-N", "--no-e2e", action="store_true", help="Disable end-to-end encryption (overrides config)")
    parser.add_argument("-m", "--model", help="Override default model")
    parser.add_argument("-s", "--store-path", help="Override store path")
    parser.add_argument("-u", "--ollama-url", help="Override Ollama API URL")
    parser.add_argument(
        "-S",
        "--server-models",
        dest="server_models",
        action="store_true",
        help="Fetch available models from the Ollama server",
    )
    # Runtime behavior flags
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose_mode",
        action="store_true",
        help="Enable verbose mode (omit brevity clause from system prompt)",
    )
    # Removed: --dry-run and --no-markdown
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for the `ollamarama-matrix` CLI.

    Parses arguments, applies overrides, optionally fetches available models
    from the server, validates configuration, and runs the application.

    Args:
        argv: Optional list of CLI arguments. Defaults to `sys.argv[1:]`.

    Returns:
        Process exit code. `0` on success, `2` on configuration or runtime
        errors during startup.
    """
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    args = parser.parse_args(argv)

    setup_logging(args.log_level)

    # Run the new app path with CLI overrides applied
    overrides = {}
    if args.ollama_url:
        overrides.setdefault("ollama", {})["api_url"] = args.ollama_url
    if args.model:
        overrides.setdefault("ollama", {})["default_model"] = args.model
    if args.store_path:
        overrides.setdefault("matrix", {})["store_path"] = args.store_path
    # timeout is fixed internally; no CLI override
    if args.e2e:
        overrides.setdefault("matrix", {})["e2e"] = True
    if args.no_e2e:
        overrides.setdefault("matrix", {})["e2e"] = False
    if args.verbose_mode:
        overrides.setdefault("ollama", {})["verbose"] = True

    try:
        cfg = load_config(args.config, overrides=overrides or None)
    except FileNotFoundError:
        print(f"Config file not found: {args.config or 'config.json'}")
        return 2
    # Optionally fetch models from server for runtime
    if args.server_models:
        try:
            from .ollama_client import OllamaClient

            client = OllamaClient(base_url=cfg.ollama.api_url.rsplit("/", 1)[0], timeout=cfg.ollama.timeout)
            models = client.list_models()
            if models:
                cfg.ollama.models = models
                if cfg.ollama.default_model not in models and cfg.ollama.default_model not in set(models.values()):
                    cfg.ollama.default_model = next(iter(sorted(models.keys())))
        except Exception as e:
            print(f"Failed to fetch models from server: {e}")
            return 2
    ok, errs = validate_config(cfg)
    if not ok:
        print("Configuration errors:")
        for e in errs:
            print(f"- {e}")
        return 2
    asyncio.run(run_app(cfg, config_path=args.config or "config.json"))
    return 0
