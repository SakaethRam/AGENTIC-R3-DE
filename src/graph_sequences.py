"""
graph_sequences.py

Stage 4 of the R3-DE pipeline: knowledge graph construction and
prompt-completion synthesis.

Builds a speaker -> trigger graph with networkx, matching the actor's
documented "speaker-to-trigger knowledge graph" feature. When that
graph ends up too sparse to be useful (e.g. very short single-speaker
input), a sequential turn-based fallback graph is built instead, so
the actor always returns a graph object rather than an empty one.

Also synthesizes the final prompt/completion pairs that make up the
`sequences` field of the actor's dataset output.
"""

from __future__ import annotations

import networkx as nx

from extract import Record

# Below this edge count, the speaker->trigger graph is considered too
# sparse to be informative on its own.
_MIN_EDGES_FOR_PRIMARY_GRAPH = 2


def build_speaker_trigger_graph(records: list[Record]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for r in records:
        graph.add_node(r.speaker, kind="speaker")
        graph.add_node(r.trigger, kind="trigger")
        graph.add_edge(r.speaker, r.trigger, intent=r.intent, weight=1)
    return graph


def build_sequential_fallback_graph(records: list[Record]) -> nx.DiGraph:
    """
    A simple turn-order chain: record[i] -> record[i+1]. Used when the
    primary speaker/trigger graph doesn't have enough structure to be
    useful on its own.
    """
    graph = nx.DiGraph()
    for i, r in enumerate(records):
        node_id = f"turn_{i}"
        graph.add_node(node_id, speaker=r.speaker, trigger=r.trigger)
        if i > 0:
            graph.add_edge(f"turn_{i - 1}", node_id)
    return graph


def build_knowledge_graph(records: list[Record]) -> nx.DiGraph:
    primary = build_speaker_trigger_graph(records)
    if primary.number_of_edges() >= _MIN_EDGES_FOR_PRIMARY_GRAPH:
        return primary
    return build_sequential_fallback_graph(records)


def _format_prompt(record: Record) -> str:
    speaker_tag = record.speaker if record.speaker else "inferred"
    return f"[{speaker_tag}] {record.original_text}"


def _format_completion(record: Record) -> str:
    intent_label = record.intent.capitalize()
    trigger_part = f" (trigger: {record.trigger})" if record.trigger else ""
    return f"[{intent_label}] {record.state}{trigger_part}"


def synthesize_sequences(records: list[Record]) -> list[dict]:
    """
    Produce the prompt/completion pairs that populate the `sequences`
    field of the dataset output.
    """
    return [
        {"prompt": _format_prompt(r), "completion": _format_completion(r)}
        for r in records
    ]


def build_metadata(records: list[Record], graph: nx.DiGraph) -> dict:
    if not records:
        return {"num_records": 0, "average_confidence": 0.0, "num_clusters_discovered": 0}

    avg_confidence = sum(r.confidence for r in records) / len(records)
    num_clusters = len({r.cluster_id for r in records if r.cluster_id is not None})
    return {
        "num_records": len(records),
        "average_confidence": round(avg_confidence, 4),
        "num_clusters_discovered": num_clusters,
        "graph_node_count": graph.number_of_nodes(),
        "graph_edge_count": graph.number_of_edges(),
    }


if __name__ == "__main__":
    from speaker_split import split_into_turns
    from extract import run_frame_extraction, cluster_records
    from causal_uncertainty import score_confidence

    sample = "Alice: Let's schedule a meeting tomorrow at 3pm.\nBob: Works for me."
    turns = split_into_turns(sample)
    records = cluster_records([run_frame_extraction(t) for t in turns])
    records = score_confidence(records)

    graph = build_knowledge_graph(records)
    sequences = synthesize_sequences(records)
    metadata = build_metadata(records, graph)

    print("sequences:", sequences)
    print("metadata:", metadata)
