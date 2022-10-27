import logging
from typing import Any

LOGGER = logging.getLogger(__name__)


def log_error(e: Any):
    LOGGER.exception("%s: %s", type(e), e)
