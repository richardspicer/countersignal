Program-level architecture notes for Volery. Individual tool architectures live in their respective repos.

---
## Program Structure

```
richardspicer/
├── volery/                         Program docs & roadmap
│   ├── concepts/
│   │   ├── CXP-Canary.md     Concept doc: coding assistant context poisoning
│   │   ├── Drongo.md           Concept doc: RAG retrieval poisoning optimizer
│   │   └── TEMPLATE.md             Concept doc template
│   ├── README.md
│   ├── Roadmap.md
│   └── Architecture.md             (this file)
│
├── IPI-Canary/                     Phase 1: Indirect prompt injection detection
│   ├── docs/
│   │   ├── Architecture.md         Full IPI-Canary architecture
│   │   └── Roadmap.md              IPI-Canary development phases
│   └── ...
│
├── CXP-Canary/               Phase 1.5: Coding assistant context poisoning (planned)
│
└── Drongo/                     Phase 2.5: RAG retrieval poisoning optimizer (planned, may be IPI-Canary module)
```

Each tool repo owns its own Architecture.md and Roadmap.md. This document covers cross-tool integration points and shared patterns.

---
## Shared Methodology

All Volery tools follow the same four-step pattern:

```mermaid
flowchart LR
    Generate[1. Generate Payload] --> Deploy[2. Deploy to Target]
    Deploy --> Track[3. Track Execution]
    Track --> Evidence[4. Capture Evidence]
    Evidence --> Generate
```

- **Generate** — Create payloads tailored to the target attack surface (documents, context files, retrieval-optimized text)
- **Deploy** — Place payloads where AI agents will ingest them (knowledge bases, repos, vector databases)
- **Track** — Listen for out-of-band callbacks proving the agent executed the payload
- **Evidence** — Capture proof-of-execution with metadata (technique, format, model, timestamp)

The callback-based verification is what differentiates Volery from output analysis tools.

---
## Cross-Tool Integration Points

### Drongo → IPI-Canary (Phase 2.5)

The primary cross-tool integration. Drongo optimizes text for vector retrieval; IPI-Canary wraps it with callback payloads.

```mermaid
flowchart LR
    EJ[Drongo] -->|retrieval-optimized text| IPC[IPI-Canary]
    IPC -->|payload documents| RAG[Target RAG System]
    RAG -->|callback| Listener[Callback Server]
```

**Integration decision deferred:** Drongo may be a standalone repo with shared payload format, or a module within IPI-Canary. The choice depends on whether Drongo has standalone research value beyond IPI-Canary integration.

### Shared Payload Format (Planned)

When Drongo development begins, define a shared format for passing retrieval-optimized text to IPI-Canary's generator pipeline. Candidates: JSON payload manifest, shared Python data model, or CLI piping.

---
## Ecosystem Context

Volery handles **content & supply chain** attacks. The **CounterAgent** program handles **protocol & system** attacks:

| Program | Attack Surface | Tools |
|---------|---------------|-------|
| **Volery** | Document ingestion, context files, vector retrieval | IPI-Canary, CXP-Canary, Drongo |
| **CounterAgent** | MCP servers, tool trust, agent delegation | mcp-audit, mcp-proxy, agent-inject, agent-chain |

The programs are complementary. Volery tests what happens when agents ingest malicious *content*. CounterAgent tests what happens when agents interact with malicious *infrastructure*. Findings from both feed into detection engineering (Wazuh/Sigma rules) and richardspicer.io publications.

---
## Framework Mapping

Each Volery tool maps to established AI security frameworks. This grounds findings in shared taxonomy for conference submissions, blog posts, and responsible disclosure.

| Tool | OWASP LLM Top 10 (2025) | OWASP Agentic Top 10 (2026) | MITRE ATLAS |
|------|--------------------------|----------------------------|-------------|
| **IPI-Canary** | LLM01: Prompt Injection | ASI-01: Agent Goal Hijacking | AML.T0051: LLM Prompt Injection |
| **CXP-Canary** | LLM01: Prompt Injection, LLM03: Supply Chain | ASI-01: Agent Goal Hijacking, ASI-03: Tool Misuse | AML.T0051: LLM Prompt Injection |
| **Drongo** | LLM08: Vector & Embedding Weaknesses | ASI-07: Knowledge Poisoning | AML.T0020: Poison Training Data |

### Mapping rationale

- **LLM01 (Prompt Injection):** IPI-Canary and CXP-Canary exploit indirect prompt injection through different delivery vectors — document ingestion (IPI-Canary) and project-level instruction files (CXP-Canary). Both inject attacker instructions via content the agent trusts.
- **LLM03 (Supply Chain):** CXP-Canary also touches supply chain risk — poisoned context files can propagate through cloned repos, open-source dependencies, and shared templates.
- **LLM08 (Vector & Embedding Weaknesses):** Added in the 2025 revision for RAG-specific attacks. Drongo directly targets this by optimizing content for retrieval ranking manipulation.
- **ASI-01 (Agent Goal Hijacking):** All three tools ultimately aim to redirect agent behavior via content the agent consumes.
- **ASI-03 (Tool Misuse):** CXP-Canary payloads can cause coding assistants to misuse their tool access (shell, file writes, API calls).
- **ASI-07 (Knowledge Poisoning):** Drongo's primary target — corrupting the retrieval knowledge base so the agent serves attacker-controlled content.

---
## Technology Stack (Shared Defaults)

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python ≥3.11 | Ecosystem alignment, ML library access |
| CLI Framework | Typer | Consistent across all tools |
| Packaging | pyproject.toml + uv | Modern Python packaging |
| Linting | Ruff | Fast, comprehensive |
| Type Checking | Mypy | `check_untyped_defs = true` |
| Git Hooks | Pre-commit | Enforced quality gates |
| Testing | pytest | Standard Python testing |

Individual tools may add stack-specific dependencies (e.g., sentence-transformers for Drongo, browser automation for CXP-Canary).

---

*This is a program-level architecture document. Full tool architectures live in each tool's repo. This document will expand as cross-tool integration points are implemented.*
