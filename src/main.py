"""
main.py

Actor entrypoint. Reads the actor's input (see .actor/input_schema.json),
runs it through the full R3-DE pipeline, and pushes one dataset item
matching .actor/dataset_schema.json.

Run locally without the Apify runtime via:
    python -m src --raw-text "Alice: Let's meet tomorrow.\nBob: Works for me."

Run as an actor (the path Docker CMD uses):
    python3 -m src
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from speaker_split import split_into_turns
from extract import run_frame_extraction, cluster_records
from causal_uncertainty import score_confidence, estimate_causal_effect
from graph_sequences import build_knowledge_graph, synthesize_sequences, build_metadata


def run_pipeline(raw_text: str) -> dict:
    """
    Run the full R3-DE pipeline over raw_text and return a dict shaped
    to match .actor/dataset_schema.json.
    """
    turns = split_into_turns(raw_text)
    records = [run_frame_extraction(t) for t in turns]
    records = cluster_records(records)
    records = score_confidence(records)

    # Causal effect estimates are computed for observability/debugging
    # but are not currently part of the published dataset schema; log
    # them rather than dropping them silently.
    causal_effects = estimate_causal_effect(records)

    graph = build_knowledge_graph(records)
    sequences = synthesize_sequences(records)
    metadata = build_metadata(records, graph)
    metadata["causal_effects"] = causal_effects

    return {
        "structured_records": [r.to_dict() for r in records],
        "sequences": sequences,
        "metadata": metadata,
    }


async def _run_as_actor() -> None:
    """
    Actor-runtime path. Imported lazily so this module can also be
    exercised as a plain library/CLI without the `apify` package
    being on the path (useful for unit tests and CI schema checks).
    """
    from apify import Actor

    async with Actor:
        actor_input = await Actor.get_input() or {}
        raw_text = actor_input.get("rawText") or ""

        if not raw_text.strip():
            Actor.log.warning("rawText was empty; nothing to process.")
            await Actor.push_data({
                "structured_records": [],
                "sequences": [],
                "metadata": {"num_records": 0, "average_confidence": 0.0, "num_clusters_discovered": 0},
            })
            return

        result = run_pipeline(raw_text)
        await Actor.push_data(result)


def _run_as_cli(raw_text: str) -> None:
    import json

    result = run_pipeline(raw_text)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the R3-DE pipeline locally.")
    parser.add_argument(
        "--raw-text",
        default=None,
        help="Raw text to process. If omitted, runs under the Apify actor runtime instead.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.raw_text is not None:
        _run_as_cli(args.raw_text)
    else:
        asyncio.run(_run_as_actor())
