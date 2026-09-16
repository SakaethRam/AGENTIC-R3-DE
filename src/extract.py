"""
extract.py

Stage 2 of the R3-DE pipeline: per-turn structured extraction, plus
semantic clustering across turns.

In production this stage is backed by the small language model (SLM)
described in docs/ARCHITECTURE.md, running under a deterministic,
inference-only contract (zero temperature, greedy decoding, bounded
token limits, schema-locked output). This module exposes that call
behind `run_frame_extraction`, and ships a rule-based fallback,
`_fallback_frame_extraction`, so the pipeline is runnable and testable
without live model access.

Swap `run_frame_extraction` for a real call to the SLM inference
endpoint; the rest of the pipeline only depends on the `Record` shape,
not on how it was produced.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from collections import defaultdict

from speaker_split import Turn

_INTENT_KEYWORDS = {
    "command": ("let's", "please", "schedule", "send", "do", "make", "set up"),
    "question": ("?",),
    "statement": (),
}

_POSITIVE_WORDS = {"great", "works", "good", "thanks", "agreed", "perfect"}
_NEGATIVE_WORDS = {"can't", "cannot", "won't", "issue", "problem", "delay", "no"}


@dataclass
class Record:
    speaker: str
    entity: str
    state: str
    trigger: str
    intent: str
    sentiment: float
    confidence: float
    original_text: str
    cluster_id: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _classify_intent(text: str) -> str:
    lowered = text.lower()
    if "?" in text:
        return "question"
    for keyword in _INTENT_KEYWORDS["command"]:
        if keyword in lowered:
            return "command"
    return "statement"


def _score_sentiment(text: str) -> float:
    lowered = text.lower()
    score = 0
    for word in _POSITIVE_WORDS:
        if word in lowered:
            score += 1
    for word in _NEGATIVE_WORDS:
        if word in lowered:
            score -= 1
    if score == 0:
        return 0.0
    return max(-1.0, min(1.0, score / 3))


def _guess_trigger_and_entity(text: str) -> tuple[str, str]:
    """
    Cheap heuristic trigger/entity guesser: the first verb-like token
    becomes the trigger, the remaining noun phrase becomes the entity.
    A real deployment defers this entirely to the SLM's frame output.
    """
    words = text.strip().rstrip(".!?").split()
    if not words:
        return "", ""
    trigger = words[0].lower()
    entity = " ".join(words[1:]) if len(words) > 1 else text
    return trigger, entity


def _fallback_frame_extraction(turn: Turn) -> Record:
    trigger, entity = _guess_trigger_and_entity(turn.text)
    intent = _classify_intent(turn.text)
    sentiment = _score_sentiment(turn.text)
    return Record(
        speaker=turn.speaker,
        entity=entity,
        state=turn.text,
        trigger=trigger,
        intent=intent,
        sentiment=sentiment,
        confidence=0.5,  # overwritten by the uncertainty stage
        original_text=turn.text,
    )


def run_frame_extraction(turn: Turn, *, use_slm: bool = False) -> Record:
    """
    Extract a structured Record from a single turn.

    Set use_slm=True once the actor is wired to the real inference
    endpoint; that path is intentionally left unimplemented here since
    it depends on deployment-specific model access.
    """
    if use_slm:
        raise NotImplementedError(
            "Wire this to the deployed SLM inference endpoint; "
            "see docs/ARCHITECTURE.md for the inference contract."
        )
    return _fallback_frame_extraction(turn)


def cluster_records(records: list[Record], *, key: str = "trigger") -> list[Record]:
    """
    Group records into semantic clusters using shared-trigger overlap
    as a cheap stand-in for embedding-based clustering. Assigns each
    record's cluster_id in place and returns the same list.
    """
    buckets: dict[str, list[Record]] = defaultdict(list)
    for record in records:
        bucket_key = getattr(record, key) or "misc"
        buckets[bucket_key].append(record)

    for cluster_id, (_, bucket) in enumerate(sorted(buckets.items())):
        for record in bucket:
            record.cluster_id = cluster_id

    return records


if __name__ == "__main__":
    from speaker_split import split_into_turns

    sample = "Alice: Let's schedule a meeting tomorrow at 3pm.\nBob: Works for me."
    turns = split_into_turns(sample)
    records = [run_frame_extraction(t) for t in turns]
    records = cluster_records(records)
    for r in records:
        print(r.to_dict())
