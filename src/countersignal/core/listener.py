"""Shared callback listener infrastructure.

Core scoring and hit recording logic used by the callback listener
server. Display formatting stays in the module-specific server code.
"""

import re

from countersignal.core import db
from countersignal.core.models import Hit, HitConfidence

# User-Agent patterns that suggest programmatic HTTP clients (not browsers/scanners)
_PROGRAMMATIC_UA_PATTERNS = re.compile(
    r"python-requests|httpx|aiohttp|urllib|curl|wget|node-fetch|"
    r"axios|got/|undici|fetch|llm|openai|langchain",
    re.IGNORECASE,
)


def score_confidence(token_valid: bool, user_agent: str) -> HitConfidence:
    """Score hit confidence based on token validity and User-Agent analysis.

    Confidence rubric:
        HIGH: Valid campaign token present — strong proof of agent execution.
        MEDIUM: No/invalid token, but User-Agent matches known programmatic
            HTTP clients (python-requests, httpx, curl, etc.).
        LOW: No/invalid token and browser or scanner User-Agent.

    Args:
        token_valid: Whether the campaign authentication token matched.
        user_agent: HTTP User-Agent header from the request.

    Returns:
        HitConfidence level for the callback.
    """
    if token_valid:
        return HitConfidence.HIGH
    if _PROGRAMMATIC_UA_PATTERNS.search(user_agent):
        return HitConfidence.MEDIUM
    return HitConfidence.LOW


def record_hit(hit: Hit) -> None:
    """Persist a hit to the database.

    Called as a background task from the callback endpoint so the
    HTTP response is returned immediately without blocking on I/O.

    Args:
        hit: Hit object to save.
    """
    db.save_hit(hit)
