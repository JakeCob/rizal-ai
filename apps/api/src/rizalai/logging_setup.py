"""Application logging (plan 008, tech debt 29).

Under uvicorn only WARNING and above used to reach stderr, so INFO records
such as reflection fallbacks never showed in Railway's logs. The API attaches
one stream handler to the `rizalai` logger at app creation, at LOG_LEVEL
(default INFO), with a plain line that carries the logger name. uvicorn's own
loggers are left alone.
"""

import logging
import sys

HANDLER_NAME = "rizalai-stream"
FORMAT = "%(levelname)s %(name)s: %(message)s"


def configure_logging(level: str) -> None:
    """Idempotent: a repeated call sets the level and reuses the handler."""
    logger = logging.getLogger("rizalai")
    logger.setLevel(level.upper())
    if any(h.get_name() == HANDLER_NAME for h in logger.handlers):
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.set_name(HANDLER_NAME)
    handler.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(handler)
