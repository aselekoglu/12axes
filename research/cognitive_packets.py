"""Deterministic 24-item cognitive interview packet generator — NO interview data.

Over 20 distinct packet indices, all 240 source questions are allocated twice
across participants (two appearances per item) under the proposed design.
These are experimental assignments, not a recruitment or study license.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import random

from research.content_review import _write_csv, verify_snapshot
from research.assignment import DEFAULT_INSTRUMENT, load_instrument

PROBES = {
    "en": (
        "In your own words, what is this statement asking?",
        "What do the important terms mean to you? Which terms seem unclear?",
        "How did you decide which answer to choose?",
        "Would the wording mean the same thing in a different political or cultural setting?",
    ),
    "pt": (
        "Com suas palavras, o que esta afirmação está perguntando?",
        "O que os termos mais importantes significam para você? Quais parecem ambíguos?",
        "Como você escolheu sua resposta?",
        "Esta frase teria o mesmo significado em outro contexto político ou cultural?",
    ),
}
COLUMNS = ["packet_id", "round_id", "instrument_version", "language", "position",
           "item_id", "axis_id", "agree_pole", "question_text", "probe_1",
           "probe_2", "probe_3", "probe_4", "comprehension_issue",
           "retrieval_issue", "judgment_issue", "response_mapping_issue",
           "moderator_observation", "review_action"]


def _seed(*parts: object) -> int:
    return int.from_bytes(hashlib.sha256("::".join(str(p) for p in parts).encode()).digest(), "big")


def make_interview_packet(index: int, language: str = "en", *, round_id: str = "draft-round-1",
                          instrument_path: Path = DEFAULT_INSTRUMENT) -> list[dict]:
    verify_snapshot(instrument_path)
    if isinstance(index, bool) or not 0 <= index <= 19:
        raise ValueError("Use one of 20 packet indices (0–19) for the planned rotation")
    if language not in ("en", "pt"):
        raise ValueError("language must be en or pt")
    if not round_id or len(round_id) > 64 or not all(c.isalnum() or c in "-_" for c in round_id):
        raise ValueError("invalid round code")
    instrument = load_instrument(instrument_path)
    by_group = {}
    for axis in instrument["axes"]:
        for pole in ("LEFT", "RIGHT"):
            by_group[(axis["id"], pole)] = sorted(
                [it for it in instrument["items"]
                 if it["axis_id"] == axis["id"] and it["agree_pole"] == pole],
                key=lambda it: it["id"])
    # Each 20-person allocation contains 2 uses of each of the 10 items per
    # axis/pole. Choice order is independent of answer content.
    chosen = [by_group[(axis["id"], pole)][index % 10]
              for axis in instrument["axes"] for pole in ("LEFT", "RIGHT")]
    order = chosen[:]
    random.Random(_seed(index, round_id, instrument["instrument_version"])).shuffle(order)
    result = []
    for position, item in enumerate(order, 1):
        row = {
            "packet_id": f"COG_{index:02d}", "round_id": round_id,
            "instrument_version": instrument["instrument_version"],
            "language": language, "position": position, "item_id": item["id"],
            "axis_id": item["axis_id"], "agree_pole": item["agree_pole"],
            "question_text": item["wording"][language],
            **{f"probe_{k}": probe for k, probe in enumerate(PROBES[language], 1)},
            "comprehension_issue": "", "retrieval_issue": "", "judgment_issue": "",
            "response_mapping_issue": "", "moderator_observation": "",
            "review_action": "",
        }
        result.append(row)
    return result


def audit_packet_rotation(language: str = "en") -> dict:
    from collections import Counter
    counts = Counter()
    for index in range(20):
        counts.update(row["item_id"] for row in make_interview_packet(index, language))
    if len(counts) != 240 or set(counts.values()) != {2}:
        raise AssertionError("Cognitive packet rotation coverage broken")
    return {"packet_count": 20, "items_per_packet": 24,
            "unique_items_covered": len(counts), "appearances_per_item": 2,
            "note": "Assignment opportunity only: not interviews completed."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=int)
    parser.add_argument("--lang", choices=("en", "pt"), default="en")
    parser.add_argument("--round", dest="round_id", default="draft-round-1")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    if args.audit:
        print(json.dumps(audit_packet_rotation(args.lang), indent=2))
        return
    if args.index is None or args.output is None:
        parser.error("packet generation requires --index and --output")
    _write_csv(args.output, COLUMNS,
               make_interview_packet(args.index, args.lang, round_id=args.round_id))
    print(f"Generated private cognitive interview packet: {args.output}")


if __name__ == "__main__":
    main()
