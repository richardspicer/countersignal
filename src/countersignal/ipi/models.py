"""IPI-specific data models for countersignal.

This module defines the IPI-specific enums used for indirect prompt injection
testing: document formats, hiding techniques, payload styles, and payload types.

Shared models (Campaign, Hit, HitConfidence, CampaignWithHits) live in
countersignal.core.models.
"""

from enum import StrEnum


class Format(StrEnum):
    """Supported document formats for payload generation.

    Each format supports different hiding techniques appropriate
    to its structure and typical processing pipelines.

    Attributes:
        PDF: Portable Document Format - Phase 1 & 2 techniques.
        IMAGE: PNG/JPG images - VLM attack surface (visible, subtle, EXIF).
        MARKDOWN: Markdown documents - HTML comments, zero-width chars.
        HTML: HTML documents - comments, hidden divs, CSS tricks.
        DOCX: Word documents - hidden text, comments, metadata.
        ICS: Calendar files - description, VALARM, X-properties.
        EML: Email files - headers, hidden HTML, attachments.

    Example:
        >>> from countersignal.ipi.models import Format
        >>> fmt = Format.PDF
        >>> fmt.value
        'pdf'
    """

    PDF = "pdf"
    IMAGE = "image"
    MARKDOWN = "markdown"
    HTML = "html"
    DOCX = "docx"
    ICS = "ics"
    EML = "eml"


class Technique(StrEnum):
    """Payload hiding techniques organized by format and phase.

    PDF Techniques (Phase 1 - Basic):
        WHITE_INK: White text on white background - invisible but extractable.
        OFF_CANVAS: Text positioned outside visible page boundaries.
        METADATA: Payload stored in PDF metadata fields (Title, Author, etc.).

    PDF Techniques (Phase 2 - Advanced):
        TINY_TEXT: 0.5pt font - below human visual threshold but parseable.
        WHITE_RECT: Text covered by opaque white rectangle overlay.
        FORM_FIELD: Hidden AcroForm field with payload as value.
        ANNOTATION: PDF annotation/comment layer containing payload.
        JAVASCRIPT: Document-level JavaScript action with embedded payload.
        EMBEDDED_FILE: Hidden file attachment stream within PDF.
        INCREMENTAL: Payload in PDF incremental update/custom metadata section.

    Image Techniques (Phase 3 - VLM Attack Surface):
        VISIBLE_TEXT: Human-readable text overlay on image.
        SUBTLE_TEXT: Low contrast, small font, or edge-placed text.
        EXIF_METADATA: Payload in EXIF metadata fields.

    Markdown Techniques (Phase 3):
        HTML_COMMENT: Payload in HTML comment tags (<!-- -->).
        LINK_REFERENCE: Payload in link reference definition.
        ZERO_WIDTH: Payload encoded using zero-width Unicode characters.
        HIDDEN_BLOCK: Payload in hidden HTML block (div with display:none).

    HTML Techniques (Phase 3):
        SCRIPT_COMMENT: Payload in JavaScript comment inside script tag.
        CSS_OFFSCREEN: Payload in element positioned off-screen with CSS.
        DATA_ATTRIBUTE: Payload in HTML data-* attribute.
        META_TAG: Payload in HTML meta tag content.

    DOCX Techniques (Phase 3):
        DOCX_HIDDEN_TEXT: Payload in text with hidden font attribute.
        DOCX_TINY_TEXT: Payload in 0.5pt font (below visual threshold).
        DOCX_WHITE_TEXT: White text on white background.
        DOCX_COMMENT: Payload in Word comment/annotation.
        DOCX_METADATA: Payload in document core properties.
        DOCX_HEADER_FOOTER: Payload in document header or footer.

    ICS Techniques (Phase 3 - Calendar Invite Attack Surface):
        ICS_DESCRIPTION: Payload in event DESCRIPTION property.
        ICS_LOCATION: Payload in event LOCATION property.
        ICS_VALARM: Payload in VALARM reminder DESCRIPTION.
        ICS_X_PROPERTY: Payload in custom X- extension property.

    EML Techniques (Phase 3 - Email Attack Surface):
        EML_X_HEADER: Payload in custom X- email header.
        EML_HTML_HIDDEN: Payload in hidden HTML div (display:none).
        EML_ATTACHMENT: Payload in text file attachment.

    Example:
        >>> from countersignal.ipi.models import Technique
        >>> technique = Technique.WHITE_INK
        >>> technique.value
        'white_ink'
    """

    # PDF Phase 1 techniques
    WHITE_INK = "white_ink"
    OFF_CANVAS = "off_canvas"
    METADATA = "metadata"

    # PDF Phase 2 techniques
    TINY_TEXT = "tiny_text"
    WHITE_RECT = "white_rect"
    FORM_FIELD = "form_field"
    ANNOTATION = "annotation"
    JAVASCRIPT = "javascript"
    EMBEDDED_FILE = "embedded_file"
    INCREMENTAL = "incremental"

    # Image Phase 3 techniques (VLM attack surface)
    VISIBLE_TEXT = "visible_text"
    SUBTLE_TEXT = "subtle_text"
    EXIF_METADATA = "exif_metadata"

    # Markdown Phase 3 techniques
    HTML_COMMENT = "html_comment"
    LINK_REFERENCE = "link_reference"
    ZERO_WIDTH = "zero_width"
    HIDDEN_BLOCK = "hidden_block"

    # HTML Phase 3 techniques
    SCRIPT_COMMENT = "script_comment"
    CSS_OFFSCREEN = "css_offscreen"
    DATA_ATTRIBUTE = "data_attribute"
    META_TAG = "meta_tag"

    # DOCX Phase 3 techniques
    DOCX_HIDDEN_TEXT = "docx_hidden_text"
    DOCX_TINY_TEXT = "docx_tiny_text"
    DOCX_WHITE_TEXT = "docx_white_text"
    DOCX_COMMENT = "docx_comment"
    DOCX_METADATA = "docx_metadata"
    DOCX_HEADER_FOOTER = "docx_header_footer"

    # ICS Phase 3 techniques (calendar invite attack surface)
    ICS_DESCRIPTION = "ics_description"
    ICS_LOCATION = "ics_location"
    ICS_VALARM = "ics_valarm"
    ICS_X_PROPERTY = "ics_x_property"

    # EML Phase 3 techniques (email attack surface)
    EML_X_HEADER = "eml_x_header"
    EML_HTML_HIDDEN = "eml_html_hidden"
    EML_ATTACHMENT = "eml_attachment"


class PayloadStyle(StrEnum):
    """Payload content styles for social engineering effectiveness.

    Styles range from obvious (for baseline testing) to subtle (for realistic
    attack simulation). More subtle styles blend the injection instruction
    into plausible document content.

    Attributes:
        OBVIOUS: Direct injection markers - easily detectable baseline.
        CITATION: Disguised as document reference or citation.
        REVIEWER: Appears as note to document reviewer/editor.
        HELPFUL: Framed as helpful supplementary resource.
        ACADEMIC: Academic or research cross-reference format.
        COMPLIANCE: Looks like compliance or verification requirement.
        DATASOURCE: Appears as data source attribution.

    Example:
        >>> from countersignal.ipi.models import PayloadStyle
        >>> style = PayloadStyle.CITATION
        >>> style.value
        'citation'
    """

    OBVIOUS = "obvious"
    CITATION = "citation"
    REVIEWER = "reviewer"
    HELPFUL = "helpful"
    ACADEMIC = "academic"
    COMPLIANCE = "compliance"
    DATASOURCE = "datasource"


class PayloadType(StrEnum):
    """Payload objectives defining the attack goal.

    Types represent different risk levels and attack objectives,
    from proof-of-execution callbacks to more dangerous actions.

    Attributes:
        CALLBACK: Simple HTTP callback - proof of execution (default, safe).
        EXFIL_SUMMARY: Attempts to exfiltrate document summary via callback.
        EXFIL_CONTEXT: Attempts to exfiltrate conversation context.
        SSRF_INTERNAL: Server-side request forgery to internal endpoints.
        INSTRUCTION_OVERRIDE: Attempts to override system instructions.
        TOOL_ABUSE: Attempts to misuse agent tools/capabilities.
        PERSISTENCE: Attempts to persist instructions across sessions.

    Note:
        Non-callback payload types require the --dangerous CLI flag and are
        intended for authorized security testing only. See docs/Roadmap.md
        for safety gating requirements.

    Example:
        >>> from countersignal.ipi.models import PayloadType
        >>> ptype = PayloadType.CALLBACK
        >>> ptype.value
        'callback'
    """

    CALLBACK = "callback"
    EXFIL_SUMMARY = "exfil_summary"
    EXFIL_CONTEXT = "exfil_context"
    SSRF_INTERNAL = "ssrf_internal"
    INSTRUCTION_OVERRIDE = "instruction_override"
    TOOL_ABUSE = "tool_abuse"
    PERSISTENCE = "persistence"
