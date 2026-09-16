# Architecture

R³-DE is organized as a sequential, multi-layer pipeline. Each layer consumes the previous layer's output and adds a new dimension of structure. This document describes the stages in the order they run and the contract each one is expected to honor.

## Pipeline overview

1. **Ingestion** — accepts raw text via the `rawText` input field. Web-scraped ingestion is planned but not yet active (see Roadmap).
2. **Speaker-aware sentence splitting** — segments input into turns and attributes each turn to a speaker where one is detectable; falls back to an inferred speaker label when none is present.
3. **Entity, action, state, and intent extraction** — identifies what is being talked about (entity), what is being done (action/trigger), the resulting state, and the communicative intent (command, question, statement, etc.) of each turn.
4. **Sentiment scoring** — assigns a sentiment value per turn.
5. **Semantic clustering** — groups related utterances so that recurring topics or threads are identifiable across a long input.
6. **Causal inference** — models trigger-to-state relationships using DoWhy combined with linear regression, so the pipeline can express that a given action plausibly caused a given state change rather than merely co-occurring with it.
7. **Uncertainty and confidence scoring** — applies Gaussian Process Regression to attach a confidence value and noise estimate to each extracted record.
8. **Knowledge graph construction** — builds a speaker-to-trigger graph with NetworkX, plus a sequential turn-based fallback graph for cases where the primary graph is sparse.
9. **Prompt-completion synthesis** — emits clean prompt/completion pairs derived from the structured records, ready for supervised fine-tuning.

## Inference contract

The extraction layers are powered by a small language model (SLM) running under a strict inference-only contract:

- No training, fine-tuning, or weight updates happen during a run.
- Generation is deterministic: zero temperature, greedy decoding, bounded token limits.
- Inputs are normalized into intent-state frames with defined roles, ordered timelines, and explicit timestamps before the model sees them.
- Outputs are enforced to be schema-compliant, strictly typed, and complete — no partially-filled records are emitted.

The practical implication for integrators: identical input produces identical output. This makes R³-DE datasets usable as regression fixtures and ground truth, not just as one-off extraction results.

## Design goals

- **Zero annotation overhead** — no ontology or label set has to be defined up front; the pipeline infers structure from the input itself.
- **Domain-agnostic** — the same pipeline runs against support chats, engineering logs, meeting transcripts, and safety reports without reconfiguration.
- **Reproducibility over creativity** — the SLM is configured as a semantic frame generator, not an open-ended text generator, which trades flexibility for auditability.

## Roadmap

- Native web scraping ingestion (currently direct raw-text input only).
- Expanded entity typing beyond the current single-label extraction.

## Where this fits in a larger system

R³-DE is designed to sit upstream of model training or agent evaluation, not as a chat interface itself. Typical placements:

- Feeding a fine-tuning job with prompt-completion pairs.
- Producing ground-truth datasets for regression-testing an existing agent.
- Populating a feature store from CSV-based, schema-locked output for downstream BI or analytics tooling.
