# Volery

**Open source offensive security suite for testing content and supply chain attacks against AI agents.**

A flock of canaries — each tool generates payloads, deploys them into AI agent pipelines, and tracks whether they execute. Covers indirect prompt injection, coding assistant context poisoning, and RAG retrieval poisoning. Proof-of-execution via out-of-band callback, not output analysis.

> Research program by [Richard Spicer](https://richardspicer.io) · [GitHub](https://github.com/richardspicer)

Volery is the **content & supply chain** arm of the Agentic AI Security ecosystem. The **CounterAgent** program ([mcp-audit](https://github.com/richardspicer/mcp-audit), mcp-proxy, agent-inject, agent-chain) is the sister program handling protocol & system security.

---

## Tools

The program produces three tools in phases, each targeting a different content-based attack surface:

| Tool | Phase | Focus | Status |
|------|-------|-------|--------|
| [**IPI-Canary**](https://github.com/richardspicer/IPI-Canary) | 1 | Indirect prompt injection via document ingestion — proof-of-execution callback tracking | 🟡 Pre-release |
| **CodeAgent-Canary** | 1.5 | Coding assistant context file poisoning — test whether project instruction files cause vulnerable code generation | 📋 Planned |
| **Embed-Ject** | 2.5 | RAG retrieval poisoning optimizer — generate documents that win vector similarity battles to guarantee payload retrieval | 📋 Planned |

---

Existing AI red teaming tools (Garak, PyRIT, Promptfoo, Spikee) focus on LLM-level testing — prompt injection, output analysis, jailbreaks. Volery targets the content layer: what happens when AI agents ingest documents, parse project files, or retrieve poisoned content from vector databases. The shared methodology across all three tools is generate → deploy → track execution via callback.

---

## Phase 1: Indirect Prompt Injection Detection — `IPI-Canary` (Active)

The anchor tool. Generates documents with hidden payloads across 7 formats (PDF, Image, Markdown, HTML, DOCX, ICS, EML) using 34 hiding techniques and listens for callbacks when AI agents execute them. Authenticated callbacks with confidence scoring provide proof-of-execution.

```bash
# Generate payloads (all formats, all techniques)
ipi-canary generate --callback http://your-server:8080 --output ./payloads/ --technique all --payload citation

# Start listener
ipi-canary listen --port 8080

# Check results
ipi-canary status
```

**Current status:** 34 techniques across 7 formats, 7 payload styles × 7 payload types (49 template combinations), authenticated callbacks with confidence scoring, HTMX web dashboard, deterministic corpus generation. 12 confirmed real-world callbacks against Open WebUI. 18 models tested across Ollama, Groq, and OpenRouter. See the [IPI-Canary repo](https://github.com/richardspicer/IPI-Canary) for details.

---

## Phase 1.5: Coding Assistant Context Poisoning — `CodeAgent-Canary` (Planned)

Tests whether poisoned project-level instruction files (CLAUDE.md, AGENTS.md, .cursorrules, copilot-instructions.md, .windsurfrules, .gemini/settings.json) cause AI coding assistants to produce vulnerable code, exfiltrate data, or execute commands.

- Generate poisoned context file corpora organized by objective (backdoor insertion, credential exfil, dependency confusion, permission escalation) and by assistant format
- Test against real coding assistants: Claude Code, Cursor, GitHub Copilot, Windsurf, Codex
- Produce assistant comparison matrices showing susceptibility by payload category
- Generate bounty-ready PoCs: minimal reproduction packages (poisoned repo + trigger prompt + evidence capture)

Completely unoccupied niche — academic research catalogs 42+ attack techniques but no packaged offensive testing tool exists.

---

## Phase 2.5: RAG Retrieval Poisoning Optimizer — `Embed-Ject` (Planned)

Solves the retrieval prerequisite that IPI-Canary assumes: how to guarantee poisoned content actually gets retrieved into the LLM's context window. Generates documents optimized to win vector similarity battles in RAG systems.

- Generate text optimized for high cosine similarity with likely user queries across common embedding models
- Wrap optimized text + injection payload into document formats (PDF, DOCX, TXT, HTML)
- Validate retrieval rank against test vector DB (ChromaDB)
- Report retrieval success rates across embedding models

Natural pairing with IPI-Canary: Embed-Ject optimizes for retrieval → IPI-Canary wraps with callback payloads → combined tool tests the full RAG attack chain.

---

## The Shared Methodology

All three tools follow the same pattern:

1. **Generate** — Create payloads tailored to the target attack surface
2. **Deploy** — Place payloads where AI agents will ingest them
3. **Track** — Listen for out-of-band callbacks proving execution
4. **Evidence** — Capture proof-of-execution with metadata for research, bounties, and disclosure

This is what separates Volery from output analysis tools. A callback proves the agent *acted*, not just that it *responded*.

---

## Framework Mapping

All findings map to established frameworks:

| Framework | Usage |
|-----------|-------|
| OWASP Top 10 for LLM Applications 2025 | Primary vulnerability taxonomy |
| OWASP Top 10 for Agentic AI | Attack pattern classification |
| MITRE ATLAS | Adversarial ML technique mapping |
| NIST AI RMF | Risk management context |

---

## Legal

All tools are intended for authorized security testing only. Only test systems you own, control, or have explicit permission to test. Responsible disclosure for all vulnerabilities discovered.

## License

All Volery tools are released under [MIT](https://opensource.org/licenses/MIT).

## Documentation

| Document | Purpose |
|----------|---------|
| [Roadmap](Roadmap.md) | Phased development plan, tool descriptions, success metrics |
| [Architecture](Architecture.md) | Program-level architecture notes and cross-tool integration points |
| [concepts/](concepts/) | Concept docs for planned tools (CodeAgent-Canary, Embed-Ject) |

## AI Disclosure

This project uses a human-led, AI-augmented workflow. See [AI-STATEMENT.md](AI-STATEMENT.md).
