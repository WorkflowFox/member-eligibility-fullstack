# AGENTS.md

## Commands

### apps/api (Python + FastAPI)

- `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt` - install dependencies
- `.venv/bin/pytest` - the whole suite
- `.venv/bin/pytest tests/test_placeholder.py` - one test file

### apps/web (Next.js + TypeScript)

- `npm install` - install dependencies
- `npm test` - the whole suite
- `npx vitest run tests/placeholder.test.ts` - one test file

## Rules

- Dependencies are added in `apps/api/requirements.txt` (or
  `requirements-dev.txt` for test-only deps) and `apps/web/package.json`.
  Do not add one without asking.
