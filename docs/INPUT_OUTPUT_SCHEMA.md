# Input and Output Schema

This page is the human-readable counterpart to `.actor/input_schema.json` and `.actor/dataset_schema.json`. Treat those files as the source of truth; this page explains intent and usage.

## Input

| Field     | Type   | Required | Description |
|-----------|--------|----------|-------------|
| `rawText` | string | No       | Raw, unstructured text: conversations, transcripts, logs, reports, or notes. Speaker labels, timestamps, intent, and structure are inferred automatically, so no pre-formatting is required. |

Notes:

- Native web-scraping ingestion (URL-in, structured-data-out) is listed as an upcoming feature on the actor and is not part of the current input contract. Until it ships, feed already-scraped or already-collected text through `rawText`.
- Because extraction is deterministic, the same `rawText` value will always produce the same structured output. Treat input as a cache key if you are building a pipeline around this actor.

## Output

Each run produces a default dataset with a single record per run, shaped as:

| Field                | Type   | Description |
|-----------------------|--------|-------------|
| `structured_records`  | array  | One entry per extracted turn/utterance, each with `speaker`, `entity`, `state`, `trigger`, `intent`, `sentiment`, `confidence`, and `original_text`. |
| `sequences`            | array  | Prompt/completion pairs derived from the structured records, ready for supervised fine-tuning. |
| `metadata`             | object | Run-level summary: `num_records`, `average_confidence`, `num_clusters_discovered`, and related aggregate stats. |

### `structured_records[]` field detail

- `speaker` — attributed or inferred speaker label.
- `entity` — the subject the turn is about.
- `state` — the resulting state expressed by the turn.
- `trigger` — the action or event driving the state.
- `intent` — the communicative function of the turn (e.g. command, question, statement).
- `sentiment` — numeric sentiment score.
- `confidence` — Gaussian Process Regression-derived confidence score for the record.
- `original_text` — the source span the record was extracted from, preserved for traceability.

### `sequences[]` field detail

- `prompt` — a formatted representation of the turn, including inferred speaker context.
- `completion` — the structured interpretation of that turn, formatted as a training target.

## Validating against the schema

Both JSON files under `.actor/` are standard JSON Schema documents. Validate a sample payload locally before wiring it into a larger pipeline:

```bash
pip install jsonschema
python -c "
import json, jsonschema
schema = json.load(open('.actor/dataset_schema.json'))
sample = json.load(open('sample_output.json'))
jsonschema.validate(sample, schema)
"
```

The CI workflow in `.github/workflows/ci.yml` runs an equivalent check against fixture data on every pull request.
