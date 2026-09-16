"""
speaker_split.py

Stage 1 of the R3-DE pipeline: speaker-aware sentence splitting.

Takes raw text (conversations, transcripts, logs) and segments it into
discrete turns, attributing each turn to a speaker where one is
detectable. When no speaker label is present in the source text, a
turn is attributed to an inferred placeholder so downstream stages
still have a stable `speaker` field to key off of.

This module has no dependency on any of the later pipeline stages and
can be tested in isolation with plain strings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Matches "Name:" or "Name -" at the start of a line, allowing for
# multi-word names and common transcript punctuation.
_SPEAKER_PREFIX = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 ._'-]{0,40}?)\s*[:\-]\s*(.*)$")

# Rough sentence boundary heuristic. Good enough for turn-internal
# splitting; not a substitute for a full sentence tokenizer, but the
# actor keeps this dependency-light on purpose.
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


@dataclass
class Turn:
    turn_id: int
    speaker: str
    text: str
    inferred_speaker: bool = False
    sentences: list[str] = field(default_factory=list)


def _split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    parts = _SENTENCE_BOUNDARY.split(text)
    return [p.strip() for p in parts if p.strip()]


def split_into_turns(raw_text: str) -> list[Turn]:
    """
    Split raw_text into speaker-attributed turns.

    Lines that open with a "Name:" or "Name -" prefix are attributed
    to that speaker. Lines without a detectable prefix are merged into
    the previous turn when one exists, or opened as a new turn under
    an inferred speaker label ("Speaker 1", "Speaker 2", ...) when
    there is no prior turn to attach to.
    """
    turns: list[Turn] = []
    inferred_counter = 0
    turn_id = 0

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        match = _SPEAKER_PREFIX.match(line)
        if match:
            speaker, rest = match.group(1).strip(), match.group(2).strip()
            turn_id += 1
            turns.append(
                Turn(
                    turn_id=turn_id,
                    speaker=speaker,
                    text=rest,
                    inferred_speaker=False,
                    sentences=_split_sentences(rest),
                )
            )
            continue

        if turns:
            # Continuation of the previous speaker's turn (e.g. a
            # wrapped line in a transcript).
            turns[-1].text = f"{turns[-1].text} {line}".strip()
            turns[-1].sentences = _split_sentences(turns[-1].text)
        else:
            inferred_counter += 1
            turn_id += 1
            turns.append(
                Turn(
                    turn_id=turn_id,
                    speaker=f"Speaker {inferred_counter}",
                    text=line,
                    inferred_speaker=True,
                    sentences=_split_sentences(line),
                )
            )

    return turns


if __name__ == "__main__":
    sample = "Alice: Let's schedule a meeting tomorrow at 3pm.\nBob: Works for me."
    for t in split_into_turns(sample):
        print(t)
