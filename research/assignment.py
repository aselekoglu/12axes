"""Reproducible, offline research-form assignment for an UNAPPROVED draft instrument.

No participant identifiers, consent, responses, analytics or network calls are handled
here. The caller must implement consent and secure persistence before fielding.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parent
DEFAULT_INSTRUMENT = ROOT / "instruments" / "draft-0.1" / "instrument.json"


def load_instrument(path: Path = DEFAULT_INSTRUMENT) -> dict:
    with path.open(encoding="utf-8") as stream:
        instrument = json.load(stream)
    validate_instrument(instrument)
    return instrument


def _seed(*parts: object) -> int:
    message = "::".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(message).digest(), "big")


def validate_instrument(instrument: dict) -> None:
    """Fail closed for altered or incomplete draft instruments."""
    version = instrument.get("instrument_version", "")
    approved_pilot = bool(re.fullmatch(r"pilot-[0-9]+\.[0-9]+", version))
    if version != "draft-0.1" and not approved_pilot:
        raise ValueError("unsupported instrument version")
    status = instrument.get("research_status")
    if status != ("APPROVED_FOR_FIELDING" if approved_pilot else "NOT_APPROVED_FOR_FIELDING"):
        raise ValueError("instrument status and version are inconsistent")
    axes = [axis["id"] for axis in instrument["axes"]]
    if len(axes) != 12 or len(set(axes)) != 12:
        raise ValueError("instrument must contain 12 unique axes")
    items = instrument["items"]
    ids = [item["id"] for item in items]
    if len(ids) != 240 or len(set(ids)) != 240:
        raise ValueError("instrument must contain 240 unique items")
    by_group = defaultdict(list)
    for item in items:
        if item["axis_id"] not in axes or item["agree_pole"] not in ("LEFT", "RIGHT"):
            raise ValueError(f"invalid axis or polarity: {item['id']}")
        if not item["wording"].get("pt") or not item["wording"].get("en"):
            raise ValueError(f"missing localized item text: {item['id']}")
        if not isinstance(item["weight"], (int, float)) or item["weight"] <= 0:
            raise ValueError(f"invalid weight: {item['id']}")
        by_group[(item["axis_id"], item["agree_pole"])].append(item["id"])
    for axis in axes:
        for pole in ("LEFT", "RIGHT"):
            if len(by_group[(axis, pole)]) != 10:
                raise ValueError(f"expected 10 items at {axis}/{pole}")
    rules = instrument["assignment"]
    if (rules.get("common_per_axis_and_pole"), rules.get("rotated_per_axis_and_pole"),
            rules.get("rotation_cycle_size"), rules.get("standard_items_per_form")) != (3, 2, 7, 120):
        raise ValueError("unsupported assignment specification")
    common = rules["common_ids"]
    if len(common) != 72 or len(set(common)) != 72 or not set(common).issubset(ids):
        raise ValueError("common items must be 72 unique known ids")
    for axis in axes:
        for pole in ("LEFT", "RIGHT"):
            if len(set(common) & set(by_group[(axis, pole)])) != 3:
                raise ValueError(f"expected 3 common items at {axis}/{pole}")
    if len(instrument["archetype_questions"]) != 5:
        raise ValueError("expected 5 separately-scored archetype questions")


def generate_form(index: int, instrument: dict, *, study_seed: str = "draft-only") -> dict:
    """Create one 72-common + 48-rotating form, without storing participant data.

    Seven consecutive form indices give each non-core item TWO appearances per
    axis/polarity group (exact counts, conditional on completed assignments).
    A rotation cycle changes the shuffled candidate ordering; actual recruitment
    must track completion and missingness separately.
    """
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        raise ValueError("index must be a nonnegative integer")
    validate_instrument(instrument)
    version = instrument["instrument_version"]
    axes = [axis["id"] for axis in instrument["axes"]]
    common = set(instrument["assignment"]["common_ids"])
    by_group = defaultdict(list)
    for item in instrument["items"]:
        by_group[(item["axis_id"], item["agree_pole"])].append(item["id"])
    cycle, slot = divmod(index, 7)
    rotated = []
    for axis in axes:
        for pole in ("LEFT", "RIGHT"):
            candidates = sorted(set(by_group[(axis, pole)]) - common)
            random.Random(_seed(study_seed, version, axis, pole, cycle)).shuffle(candidates)
            rotated.extend((candidates[(2 * slot) % 7], candidates[(2 * slot + 1) % 7]))
    selected = common | set(rotated)
    if len(rotated) != 48 or len(selected) != 120:
        raise AssertionError("invalid generated form size")
    grouped = {axis: [qid for qid in selected if qid.startswith(axis + "_")] for axis in axes}
    for axis in axes:
        if len(grouped[axis]) != 10:
            raise AssertionError(f"unexpected axis form size: {axis}")
        random.Random(_seed(study_seed, version, index, axis, "within")).shuffle(grouped[axis])
    order = []
    for wave in range(10):
        axis_order = axes[:]
        random.Random(_seed(study_seed, version, index, wave, "between")).shuffle(axis_order)
        order.extend(grouped[axis][wave] for axis in axis_order)
    return {
        "instrument_version": version,
        "form_index": index,
        "question_ids": order,
        "common_item_ids": sorted(common),
        "rotated_item_ids": sorted(rotated),
    }


def coverage_report(instrument: dict, count: int, *, study_seed: str = "draft-only") -> dict:
    if count <= 0:
        raise ValueError("count must be positive")
    frequencies = Counter()
    for index in range(count):
        frequencies.update(generate_form(index, instrument, study_seed=study_seed)["question_ids"])
    common = set(instrument["assignment"]["common_ids"])
    return {
        "instrument_version": instrument["instrument_version"],
        "assigned_forms": count,
        "common_min": min(frequencies[qid] for qid in common),
        "common_max": max(frequencies[qid] for qid in common),
        "rotated_min": min(frequencies[qid] for qid in frequencies if qid not in common),
        "rotated_max": max(frequencies[qid] for qid in frequencies if qid not in common),
        "total_answer_slots": sum(frequencies.values()),
        "important": "Assignment counts are not completed responses; no inferential sample guarantees.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=int, help="print one assigned research form")
    parser.add_argument("--coverage", type=int, help="audit assignment counts across N forms")
    parser.add_argument("--study-seed", default="draft-only")
    args = parser.parse_args()
    if (args.index is None) == (args.coverage is None):
        parser.error("provide exactly one of --index or --coverage")
    instrument = load_instrument()
    result = (generate_form(args.index, instrument, study_seed=args.study_seed)
              if args.index is not None else coverage_report(instrument, args.coverage, study_seed=args.study_seed))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
