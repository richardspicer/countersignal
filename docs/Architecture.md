# Architecture

## Package Structure

```
src/countersignal/
├── __init__.py               # Package version (0.1.0)
├── __main__.py               # python -m countersignal support
├── cli.py                    # Root Typer app — mounts ipi, cxp, rxp
├── core/                     # Shared callback infrastructure
│   ├── models.py             # Campaign, Hit, HitConfidence (Pydantic)
│   ├── db.py                 # SQLite CRUD for campaigns/hits (~/.countersignal/ipi.db)
│   ├── listener.py           # Callback confidence scoring + hit recording
│   └── evidence.py           # Shared evidence patterns (stub)
├── ipi/                      # Indirect prompt injection module
│   ├── cli.py                # generate, listen, status, techniques, formats, export, reset
│   ├── models.py             # Format, Technique, PayloadStyle, PayloadType (IPI-specific enums)
│   ├── generate_service.py   # Payload generation orchestrator
│   ├── generators/           # Format-specific generators (pdf, image, markdown, html, docx, ics, eml)
│   ├── server.py             # FastAPI callback server with dashboard routes
│   ├── api.py                # API router
│   ├── ui.py                 # UI router (HTMX dashboard)
│   ├── static/               # CSS, htmx.min.js
│   └── templates/            # Jinja2 templates for dashboard
├── cxp/                      # Context file poisoning module
│   ├── cli.py                # objectives, formats, techniques, generate, validate, record, campaigns, report
│   ├── models.py             # Objective, AssistantFormat, Technique, Rule, BuildResult (dataclasses)
│   ├── builder.py            # Test repository generator
│   ├── catalog.py            # Rule catalog loader (built-in + user rules)
│   ├── base_loader.py        # Base template loading, rule insertion, marker stripping
│   ├── evidence.py           # SQLite evidence store (~/.countersignal/cxp.db)
│   ├── validator.py          # Output validation against detection rules
│   ├── reporter.py           # Comparison matrix and PoC package generation
│   ├── bases/                # Clean base templates (one per format, with section markers)
│   │   ├── cursorrules.txt   # .cursorrules (Cursor) — plaintext
│   │   ├── claude-md.md      # CLAUDE.md (Claude Code) — markdown
│   │   ├── copilot-instructions.md  # copilot-instructions.md (GitHub Copilot) — markdown
│   │   ├── agents-md.md      # AGENTS.md (Codex CLI) — markdown
│   │   ├── gemini-md.md      # GEMINI.md (Gemini CLI) — markdown
│   │   └── windsurfrules.txt # .windsurfrules (Windsurf) — plaintext
│   ├── rules/                # Built-in insecure coding rule definitions (YAML)
│   │   ├── weak-crypto-md5.yaml
│   │   ├── hardcoded-secrets.yaml
│   │   ├── no-csrf.yaml
│   │   ├── shell-true.yaml
│   │   ├── stack-traces.yaml
│   │   ├── extra-index-url.yaml
│   │   ├── insecure-perms.yaml
│   │   └── outbound-exfil.yaml
│   ├── formats/              # Assistant format definitions
│   │   ├── agents_md.py      # AGENTS.md (Gemini CLI)
│   │   ├── claude_md.py      # CLAUDE.md (Claude Code)
│   │   ├── copilot_instructions.py  # .github/copilot-instructions.md
│   │   ├── cursorrules.py    # .cursorrules (Cursor)
│   │   ├── gemini_md.py      # GEMINI.md (Gemini)
│   │   └── windsurfrules.py  # .windsurfrules (Windsurf)
│   ├── objectives/           # Attack objective definitions
│   │   ├── backdoor.py       # Backdoor insertion
│   │   ├── cmdexec.py        # Command execution
│   │   ├── depconfusion.py   # Dependency confusion
│   │   ├── exfil.py          # Credential exfiltration
│   │   └── permescalation.py # Permission escalation
│   └── techniques/           # Jinja2 templates + skeleton project files
└── rxp/                      # RAG retrieval poisoning module
    ├── __init__.py           # Module docstring
    ├── _deps.py              # Optional dependency guard
    ├── cli.py                # Typer CLI (list-models, list-profiles, validate)
    ├── collection.py         # RetrievalCollection (ChromaDB wrapper)
    ├── embedder.py           # Embedder abstraction (sentence-transformers)
    ├── models.py             # Data models (dataclasses)
    ├── registry.py           # Embedding model registry and resolution
    ├── validator.py          # Validation engine orchestration
    └── profiles/             # Built-in domain profiles
        ├── __init__.py       # Profile loader
        └── hr_policy/        # HR policy test scenario
```

## CLI Hierarchy

```
countersignal
├── ipi            # Indirect prompt injection via document ingestion
│   ├── generate   # Generate payload documents
│   ├── listen     # Start callback listener server
│   ├── status     # Show campaign status and hits
│   ├── techniques # List available hiding techniques
│   ├── formats    # List supported document formats
│   ├── export     # Export campaign data
│   └── reset      # Clear all campaigns and generated files
├── cxp            # Coding assistant context file poisoning
│   ├── objectives # List attack objectives
│   ├── formats    # List assistant format targets
│   ├── techniques # List technique matrix
│   ├── generate   # Generate poisoned test repositories
│   ├── validate   # Validate captured output against rules
│   ├── record     # Record test result into evidence store
│   ├── campaigns  # List campaigns and results
│   └── report
│       ├── matrix # Generate comparison matrix
│       └── poc    # Export bounty-ready PoC package
└── rxp            # RAG retrieval poisoning
    ├── list-models   # List available embedding models
    ├── list-profiles # List domain profiles
    └── validate      # Validate retrieval poisoning
```

## Core Module

The `core/` package provides shared infrastructure used primarily by IPI, with hooks for future RXP integration.

**Models** (`core/models.py`): Pydantic `BaseModel` classes for callback tracking:
- `Campaign` — tracks a test campaign with ID, name, creation timestamp, and callback URL
- `Hit` — records a single callback event with timestamp, source IP, User-Agent, and confidence level
- `HitConfidence` — enum (HIGH, MEDIUM, LOW) based on token validity and User-Agent analysis

**Database** (`core/db.py`): SQLite CRUD operations for campaigns and hits, stored at `~/.countersignal/ipi.db`. Uses PRAGMA user_version for schema migrations (currently v4). Automatic directory creation on first access.

**Listener** (`core/listener.py`): Callback confidence scoring logic. Analyzes incoming callbacks to determine whether they represent genuine agent execution (HIGH — valid token + non-browser User-Agent), possible execution (MEDIUM — valid token but browser User-Agent), or noise (LOW — invalid token).

**Evidence** (`core/evidence.py`): Stub for shared evidence collection patterns. Will be populated when a second module needs common evidence infrastructure.

## IPI Module

IPI (Indirect Prompt Injection) tests whether AI agents execute hidden instructions when ingesting documents.

- **34 hiding techniques** across **7 document formats** (PDF, Image, Markdown, HTML, DOCX, ICS, EML)
- **7 payload styles** (invisible text, metadata injection, steganography, etc.) x **7 payload types** (callback, exfil, SSRF, etc.) = 49 template combinations
- FastAPI-based callback server with HTMX dashboard for campaign monitoring
- Authenticated callbacks with per-campaign cryptographic tokens
- Dangerous payload gating — exfil, SSRF, and behavior modification payloads require explicit `--dangerous` flag
- Deterministic seed-based corpus generation for reproducible testing

### IPI Data Flow

```
generate → documents with hidden payloads
    ↓
deploy to AI agent (manual or via harness)
    ↓
agent ingests document → executes hidden instruction → callback
    ↓
listener receives callback → confidence scoring → hit recorded
    ↓
status/dashboard shows campaign results with evidence
```

### IPI Multi-Model Testing

IPI campaigns target multiple model backends and report per-model callback results in the existing campaign format. The callback tracker already distinguishes per-campaign tokens — extending to per-model tracking is additive. Same payload, same platform, different model backend. Results feed the existing dashboard and export formats with per-model breakdown.

## CXP Module

CXP (Context File Poisoning) is a research harness for studying whether poisoned project instruction files cause AI coding assistants to produce vulnerable code. The researcher composes payloads interactively via a TUI or CLI, the tool assembles them into realistic context files, and the evidence pipeline handles everything after the test.

- **Rule catalog** — 8 built-in insecure coding rules (YAML) + user-defined rules in `~/.countersignal/cxp/rules/`
- **6 base templates** — Clean, legitimate assistant config files with section markers for rule insertion
- **Builder engine** — Assembles context files from base templates + selected rules, generates project skeletons and prompt reference guides
- **TUI** — Textual-based interactive interface for the full build → test → record workflow
- **Evidence store** — SQLite at `~/.countersignal/cxp.db` with campaigns, test results, and validation outcomes
- **Validator** — Detection rules that check captured assistant output for compliance with inserted rules
- **Reporter** — Comparison matrix (markdown/JSON) across assistants + PoC package export (ZIP with reproduction steps)

### CXP Data Flow

```
TUI or CLI → select format + rules from catalog
    ↓
builder → load base template → insert rules at section markers → strip markers
    ↓
output → assembled context file + project skeleton + prompt reference + manifest
    ↓
researcher → opens repo in coding assistant → issues trigger prompt → captures output
    ↓
record → evidence store (campaign + test result + rules_inserted + format_id)
    ↓
validate → detection rules check captured output
    ↓
report → comparison matrix or bounty-ready PoC package
```

## RXP Module

RXP (RAG Retrieval Poisoning) validates whether adversarial documents achieve retrieval rank in vector similarity searches. It measures the retrieval prerequisite for content injection — guaranteeing poisoned content wins the vector similarity battle before IPI payloads execute.

- **Embedding model registry** with 3 built-in models + arbitrary HuggingFace model passthrough
- **ChromaDB-backed validation engine** — ephemeral collections for clean-room retrieval testing
- **Domain profiles** — YAML-defined test scenarios with corpus, poison documents, and queries
- **Optional heavy dependencies** — `chromadb` and `sentence-transformers` gated behind `require_rxp_deps()`; CLI help and listing commands work without them

### RXP Data Flow

```
validate → resolve model from registry (or ad-hoc HuggingFace name)
    ↓
load domain profile → corpus + poison documents + queries
    ↓
create Embedder (sentence-transformers, process-cached)
    ↓
create RetrievalCollection (ephemeral ChromaDB, UUID-suffixed)
    ↓
ingest corpus + poison documents → encode and store vectors
    ↓
run queries → nearest-neighbor search → poison rank per query
    ↓
aggregate → ValidationResult (retrieval rate, mean poison rank)
```

## Database Architecture

Two separate SQLite databases in `~/.countersignal/`:

### ipi.db (core/db.py)

Managed by the shared core module. Schema version tracked via `PRAGMA user_version` (currently v4).

| Table | Purpose |
|-------|---------|
| `campaigns` | Test campaigns with ID, name, callback URL, timestamps |
| `hits` | Callback events with campaign FK, confidence, source IP, User-Agent |

### cxp.db (cxp/evidence.py)

Managed independently by the CXP module. Uses its own schema and dataclass models. Schema version tracked via `PRAGMA user_version`.

| Table | Purpose |
|-------|---------|
| `campaigns` | CXP test campaigns with ID, name, description, timestamps |
| `test_results` | Captured assistant outputs with technique, assistant, model, rules_inserted, format_id, validation status, and raw output |

Both databases use `Path.home() / ".countersignal"` with automatic directory creation on first access.
