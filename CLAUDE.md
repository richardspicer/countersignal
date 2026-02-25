# countersignal

Agentic AI content & supply chain attack toolkit. Monorepo consolidating IPI-Canary, CXP-Canary, and future RXP into one Python package with a unified CLI.

## Status

Phase A scaffold — no source code yet. See `docs/Architecture-Decision.md` for migration design.

## Code Standards

- Python >=3.11, src/ layout, hatchling build
- Typer CLI, ruff linter, mypy type checker
- Google-style docstrings, 100 char line length
- Never commit to main. Feature branches only.

## Shell Quoting (CRITICAL)

CMD corrupts `git commit -m "message with spaces"`. Always use:
```
echo "feat: description here" > .commitmsg
git commit -F .commitmsg
del .commitmsg
```

## Claude Code Guardrails

- Do not create PRs. Push the branch and stop.
- Do not install new global/system CLI tools.
- Do not create plan files in the repo. Use OS temp directory if needed.
- If verification fails after 2 attempts, commit and report. Don't spin.
- Kill orphaned processes before test runs.
