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
    parser = argparse.ArgumentParser(
        prog="ollamarama-matrix",
        description=(
            "Ollamarama Matrix bot. Modern CLI that validates config and runs the app."
        ),
        add_help=True,
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("OLLAMARAMA_LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level for the launcher.",
    )
    # Accept common flags; used only for --dry-run in Phase 2.
    parser.add_argument("--config", help="Path to config.json (default: ./config.json)")
    parser.add_argument("--e2e", action="store_true", help="Enable end-to-end encryption (overrides config)")
    parser.add_argument("--no-e2e", action="store_true", help="Disable end-to-end encryption (overrides config)")
    parser.add_argument("--model", help="Override default model (dry-run only at this phase)")
    parser.add_argument("--store-path", help="Override store path (dry-run only at this phase)")
    parser.add_argument("--ollama-url", help="Override Ollama API URL (dry-run only at this phase)")
    parser.add_argument("--timeout", type=int, help="HTTP timeout seconds (dry-run only at this phase)")
    parser.add_argument(
        "--models-from-server",
        action="store_true",
        help="Fetch available models from the Ollama server instead of using config",
    )
    parser.add_argument("--no-markdown", action="store_true", help="Disable Markdown formatting (reserved)")
    parser.add_argument("--dry-run", action="store_true", help="Validate configuration and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print effective (redacted) configuration on dry-run")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    args = parser.parse_args(argv)

    setup_logging(args.log_level)

    if args.dry_run:
        overrides = {}
        if args.ollama_url:
            overrides.setdefault("ollama", {})["api_url"] = args.ollama_url
        if args.model:
            overrides.setdefault("ollama", {})["default_model"] = args.model
        if args.store_path:
            overrides.setdefault("matrix", {})["store_path"] = args.store_path
        if args.timeout is not None:
            overrides.setdefault("ollama", {})["timeout"] = int(args.timeout)
        if args.e2e:
            overrides.setdefault("matrix", {})["e2e"] = True
        if args.no_e2e:
            overrides.setdefault("matrix", {})["e2e"] = False
        if args.no_markdown:
            overrides["markdown"] = False
        try:
            cfg = load_config(args.config, overrides=overrides)
        except FileNotFoundError:
            print(f"Config file not found: {args.config or 'config.json'}")
            return 2
        except Exception as e:
            print(f"Failed to load config: {e}")
            return 2

        # Optionally fetch models from server
        if args.models_from_server:
            try:
                from .ollama_client import OllamaClient

                client = OllamaClient(base_url=cfg.ollama.api_url.rsplit("/", 1)[0], timeout=cfg.ollama.timeout)
                models = client.list_models()
                if models:
                    cfg.ollama.models = models
                    # Ensure default_model exists in mapping; fall back to first available
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
        print("Configuration OK")
        if args.verbose:
            print(json.dumps(summarize(cfg), indent=2))
        return 0

    # Run the new app path with CLI overrides applied
    overrides = {}
    if args.ollama_url:
        overrides.setdefault("ollama", {})["api_url"] = args.ollama_url
    if args.model:
        overrides.setdefault("ollama", {})["default_model"] = args.model
    if args.store_path:
        overrides.setdefault("matrix", {})["store_path"] = args.store_path
    if args.timeout is not None:
        overrides.setdefault("ollama", {})["timeout"] = int(args.timeout)
    if args.e2e:
        overrides.setdefault("matrix", {})["e2e"] = True
    if args.no_e2e:
        overrides.setdefault("matrix", {})["e2e"] = False
    if args.no_markdown:
        overrides["markdown"] = False

    try:
        cfg = load_config(args.config, overrides=overrides or None)
    except FileNotFoundError:
        print(f"Config file not found: {args.config or 'config.json'}")
        return 2
    # Optionally fetch models from server for runtime
    if args.models_from_server:
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
