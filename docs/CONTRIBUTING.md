# Contributing

This document covers local setup for developers who want to inspect, test, or extend the R³-DE actor definition.

## Prerequisites

- Docker and Docker Compose
- An Apify account and API token (only needed to trigger real remote runs; schema and lint checks work offline)
- Python 3.11+ if you are validating schemas or writing test fixtures directly

## Local setup

```bash
git clone <this-repo-url>
cd r3-de
cp .env.example .env        # add your APIFY_TOKEN if you plan to run against the platform
docker compose up --build
```

`docker-compose.yml` starts a lightweight harness that validates `.actor/actor.json`, `.actor/input_schema.json`, and `.actor/dataset_schema.json` against JSON Schema, then runs the fixture-based smoke test.

## Making changes

1. Branch from `main`.
2. If you are changing the input or output contract, update the corresponding file under `.actor/` **and** the matching section in `docs/INPUT_OUTPUT_SCHEMA.md` in the same commit. Docs and schema drifting apart is treated as a broken PR.
3. Add or update a fixture under `tests/fixtures/` that exercises the change.
4. Run the local harness (`docker compose up --build`) and confirm it passes before opening a PR.

## Commit and PR conventions

- Keep commits scoped to one logical change.
- PR titles should state the affected layer, e.g. `causal-inference: fix trigger detection for negated statements`.
- Every PR touching `.actor/` must pass the `schema-validate` and `smoke-test` jobs in `.github/workflows/ci.yml` before review.

## Reporting issues

Use the Issues tab on this repository for anything related to documentation, schema mismatches, or integration questions. For billing or platform-level problems (run failures on Apify's infrastructure, account issues), use the Issues tab on the actor's Apify Store listing instead: https://apify.com/gunmetal/r3-de/issues/open

## Code of conduct

Be direct, be specific, and keep discussion focused on the pipeline's behavior and contracts. Disagreements about design should reference the inference contract in `docs/ARCHITECTURE.md` rather than personal preference.
