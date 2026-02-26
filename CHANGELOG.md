# Changelog

All notable changes to CounterSignal will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - 2026-02-25

### Added
- Unified monorepo consolidating IPI and CXP modules into a single `countersignal` package
- Unified CLI: `countersignal ipi`, `countersignal cxp`, `countersignal rxp` (stub)
- Shared callback infrastructure in `core/` (models, db, listener)
- Centralized DB storage in `~/.countersignal/` (ipi.db, cxp.db)
- Pre-commit hooks: ruff, mypy, gitleaks, trailing whitespace
- 104 tests across IPI and CXP modules

### Changed
- IPI source migrated to `src/countersignal/ipi/`
- CXP source migrated to `src/countersignal/cxp/` with Click-to-Typer conversion
- CXP database moved from working directory to `~/.countersignal/cxp.db`
- IPI database moved from `~/.countersignal/canary.db` to `~/.countersignal/ipi.db`

### Removed
- Separate standalone CLI entry points (replaced by `countersignal ipi` and `countersignal cxp`)
- Click dependency (CXP converted to Typer)
