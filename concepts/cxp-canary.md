# CXP-Canary

> Context poisoning tester for AI coding assistants.

## Purpose

AI coding assistants treat project-level instruction files (CLAUDE.md, AGENTS.md, .cursorrules, copilot-instructions.md, .windsurfrules, .gemini/settings.json) as trusted context, but these files live in repositories that may be forked, cloned from untrusted sources, or contributed to by external parties. No packaged offensive testing tool exists to systematically test whether poisoned instruction files cause coding assistants to produce vulnerable code, exfiltrate data, or execute commands. Academic research (arxiv 2601.17548v1) catalogs 42+ attack techniques, but practitioners have no tool to reproduce, measure, or bounty-submit these findings. CXP-Canary fills that gap.

## Program Context

Phase 1.5 in the Volery program. IPI-Canary (Phase 1) handles indirect prompt injection via document ingestion — different attack surface (knowledge bases, RAG pipelines) and different victims (end users interacting with AI agents). CXP-Canary targets the developer toolchain — poisoned project files in cloned repos that affect the code developers write with AI assistance.

Both tools share the Volery methodology: generate payload → deploy → track execution. CXP-Canary's "callback" is the measurable output: did the assistant produce vulnerable code, exfiltrate credentials, or execute a command?

Findings feed into detection engineering (Sigma/Wazuh rules for context file poisoning patterns) and into the CounterAgent program's agent-inject tool (which tests tool poisoning at the MCP protocol level — complementary but different attack surface).

## Core Capabilities

- Generate poisoned context file corpora organized by objective (backdoor insertion, credential exfil, dependency confusion, permission escalation) and by assistant format (CLAUDE.md, .cursorrules, etc.).
- Interact with coding assistants headlessly to test payload effectiveness — submit trigger prompts and capture generated code.
- Detect whether generated code contains the intended vulnerability (regex, AST analysis, or execution-based validation).
- Produce behavioral test results (JSON) showing which payloads caused which assistants to produce vulnerable code, with exact prompts and outputs.
- Generate assistant comparison matrices: success rates across Claude Code, Cursor, GitHub Copilot, Windsurf, Codex.
- Package bounty-ready PoCs: minimal reproduction packages (poisoned repo + trigger prompt + evidence capture).

## Key Design Decisions

- **Standalone repo** (`richardspicer/CXP-Canary`). Different attack surface, different victims, and different testing methodology from IPI-Canary. Shares the "canary" concept (generate → deploy → track) but the implementation is entirely distinct.
- **Payload corpus organized by objective AND by assistant format.** Same backdoor insertion objective needs different file formats for different assistants. The matrix is objective × format.
- **Headless assistant interaction is required.** Manual testing doesn't scale across assistants and payload combinations. The tool must automate prompt submission and output capture. Implementation approach TBD — may be API-based for cloud assistants and CLI-based for local tools.
- **Output validation is a first-class feature.** "The assistant generated code" isn't evidence. The tool must verify the generated code contains the intended vulnerability. This is the equivalent of IPI-Canary's callback — the proof-of-execution.
- **Low implementation complexity by design.** No GPU, no model access needed for the core tool. Payload generation + headless interaction + output capture.

## Open Questions

- **Headless interaction approach:** API-based (where available) vs. terminal automation (for CLI tools like Claude Code) vs. IDE automation (for Cursor, Windsurf)? Each assistant may need a different interaction adapter. How to keep this maintainable as new assistants emerge?
- **Output validation methodology:** Regex pattern matching for known vulnerability signatures? AST analysis for structural vulnerabilities? Execution in a sandbox to test behavior? The choice affects accuracy and complexity. Leaning toward layered: regex for fast triage, AST for confirmation, sandbox for edge cases.
- **Scope of "poisoned file":** Just the instruction file itself, or also adjacent project files that provide context (requirements.txt with malicious dependencies, README.md with misleading architecture descriptions)? Broader scope is more realistic but significantly more complex.
- **Multi-file poisoning:** The AGENTS.md consolidation trend means one file can affect multiple assistants. Should CXP-Canary test multi-assistant scenarios (same repo tested against Claude Code, Cursor, Copilot simultaneously)?
- **Ethical boundaries:** Testing against cloud assistants means submitting malicious content to vendor APIs. Where's the line between security testing and abuse? Need clear responsible use policy and opt-in vendor engagement strategy.

## Artifacts

- Poisoned context file corpus organized by objective and assistant format.
- Behavioral test results (JSON): payload → assistant → generated code → vulnerability assessment.
- Assistant comparison matrix: success rates per objective per assistant.
- Bounty-ready PoC packages: minimal reproduction repos with poisoned files, trigger prompts, and evidence capture scripts.
- Responsible disclosure packages for novel vulnerabilities discovered during testing.

## Relation to Other Tools

- **IPI-Canary** tests document ingestion attacks against AI agents (RAG pipelines, knowledge bases). CXP-Canary tests project file poisoning against coding assistants. Different attack surface, different victims, same methodology.
- **Drongo** (Phase 2.5) handles RAG retrieval optimization. Not relevant to CXP-Canary — coding assistants don't use vector retrieval for project context files.
- **agent-inject** (CounterAgent Phase 2) tests tool poisoning at the MCP protocol level — malicious tool descriptions and outputs. CXP-Canary operates at the filesystem level — malicious project files. Complementary findings: agent-inject tests the agent runtime, CXP-Canary tests the development environment.
- **Garak / PyRIT** test LLM-level vulnerabilities (jailbreaks, output analysis). CXP-Canary tests the application layer above the LLM — what happens when the model receives poisoned context through its normal instruction channel.

---

*This is a concept doc, not an architecture doc. It captures intent and constraints. The full Architecture doc gets written when development begins.*
