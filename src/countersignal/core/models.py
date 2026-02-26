"""Shared data models for callback tracking.

Campaign and Hit are the canonical models for tracking payload
documents and callback hits across all CounterSignal modules.
IPI, CXP, and RXP all share this callback infrastructure.
"""

import secrets
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class HitConfidence(StrEnum):
    """Confidence level for callback hit authenticity.

    Used to distinguish genuine agent callbacks from scanner noise,
    based on token validation, User-Agent analysis, and request shape.

    Attributes:
        HIGH: Valid campaign token present — strong proof of execution.
        MEDIUM: No/invalid token, but programmatic User-Agent (python-requests, etc.).
        LOW: No/invalid token, browser or scanner User-Agent.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Campaign(BaseModel):
    """A generated payload campaign tracking document and callback info.

    Attributes with IPI-specific semantics (format, technique,
    payload_style, payload_type) are stored as strings. Each module
    defines its own enums and passes StrEnum values, which serialize
    to strings automatically.

    Attributes:
        uuid: Unique identifier for the campaign (used in callback URL).
        token: Per-campaign authentication secret for callback validation.
        filename: Generated document filename.
        output_path: Full filesystem path to the generated document.
            Set by generate_service after creation. None for legacy campaigns.
        format: Document format (e.g., "pdf", "image", "markdown").
        technique: Hiding technique used (e.g., "white_ink", "metadata").
        payload_style: Social engineering style (e.g., "obvious", "citation").
        payload_type: Attack objective type (e.g., "callback", "exfil_summary").
        callback_url: Full URL that will be triggered if payload executes.
        created_at: UTC timestamp when campaign was created.
    """

    uuid: str
    token: str = Field(default_factory=lambda: secrets.token_urlsafe(16))
    filename: str
    output_path: str | None = None
    format: str = "pdf"
    technique: str
    payload_style: str = "obvious"
    payload_type: str = "callback"
    callback_url: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Hit(BaseModel):
    """A callback hit received from an AI agent executing a payload.

    Records details of incoming HTTP requests to the callback server,
    providing proof-of-execution evidence.

    Attributes:
        id: Database row ID (None until persisted).
        uuid: Campaign UUID this hit belongs to.
        source_ip: IP address of the requesting client.
        user_agent: HTTP User-Agent header value.
        headers: Complete HTTP headers dictionary.
        body: Captured request data (query params for GET, body for POST).
            None for simple callback hits with no exfil data.
        token_valid: Whether the campaign authentication token was present and valid.
        confidence: Hit confidence level based on token validity and request analysis.
        timestamp: UTC timestamp when hit was received.
    """

    id: int | None = None
    uuid: str
    source_ip: str
    user_agent: str
    headers: dict
    body: str | None = None
    token_valid: bool = False
    confidence: HitConfidence = HitConfidence.LOW
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CampaignWithHits(BaseModel):
    """Campaign with associated callback hits for reporting.

    Combines a Campaign with its list of received Hits for
    status reporting and analysis.

    Attributes:
        campaign: The Campaign instance.
        hits: List of Hit instances received for this campaign.
    """

    campaign: Campaign
    hits: list[Hit] = []
