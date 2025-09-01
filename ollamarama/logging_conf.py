import logging
import logging.config


def setup_logging(level: str = "INFO", json: bool = False) -> None:
    """Configure logging exactly like the original script.

    - Disable existing loggers so only our format emits
    - Set root level and format
    """
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": True,
    })
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s" if json else "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=lvl, format=fmt)
