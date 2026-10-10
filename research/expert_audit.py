"""Independent evidence coding of historic actors (never infer missing views as neutral).

Records belong to a separately governed expert-research workflow. This tool
validates provenance and summarizes disagreement; it is not a source of ground truth.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from urllib.parse import urlparse

ANSWERS = {"DT", "D", "N", "C", "CT"}
STATES = {"OBSERVED", "INFERRED", "UNKNOWN", "NOT_APPLICABLE"}
AXES = ["estrutura", "representacao", "poder", "imigracao", "diplomacia",
        "intervencao", "economia", "controle", "comercio", "religiao", "moral", "tecnologia"]


def validate_audit(document: dict) -> None:
    for key in ("profile_id", "reference_period", "instrument_version", "ratings"):
        if key not in document:
            raise ValueError(f"missing {key}")
    if not document["profile_id"] or not document["reference_period"]:
        raise ValueError("profile and reference period are required")
    ratings = document["ratings"]
    if not isinstance(ratings, list):
        raise ValueError("ratings must be a list")
    seen = set()
    for index, row in enumerate(ratings):
        rater = row.get("rater_id", "")
        qid = row.get("question_id", "")
        axis = row.get("axis_id", "")
        state = row.get("evidence_state")
        answer = row.get("answer")
        sources = row.get("sources", [])
        if not rater or len(rater) > 128:
            raise ValueError(f"invalid rater at {index}")
        if axis not in AXES or not qid.startswith(axis + "_"):
            raise ValueError(f"invalid axis or item id at {index}")
        if state not in STATES:
            raise ValueError(f"invalid evidence_state at {index}")
        if state in ("UNKNOWN", "NOT_APPLICABLE") and answer is not None:
            raise ValueError(f"unknown or inapplicable answer must be null at {index}")
        if state in ("OBSERVED", "INFERRED") and answer not in ANSWERS:
            raise ValueError(f"known assessment requires valid answer at {index}")
        if not isinstance(sources, list):
            raise ValueError(f"sources must be a list at {index}")
        if state == "OBSERVED" and len(sources) == 0:
            raise ValueError(f"observed opinion requires evidence at {index}")
        for source in sources:
            parsed = urlparse(source.get("url", ""))
            if parsed.scheme != "https" or not parsed.hostname:
                raise ValueError(f"non-HTTPS evidence link at {index}")
            if not source.get("date") or not source.get("note"):
                raise ValueError(f"dated source and contextual note required at {index}")
        key = (rater, qid)
        if key in seen:
            raise ValueError(f"duplicate independent rating: {key}")
        seen.add(key)


def summarize_audit(document: dict) -> dict:
    validate_audit(document)
    ratings = document["ratings"]
    status_counts = Counter(row["evidence_state"] for row in ratings)
    by_question = defaultdict(list)
    for row in ratings:
        by_question[row["question_id"]].append(row)
    multi_rater_items = 0
    exact_agreement_items = 0
    disputed_items = []
    for qid, rows in by_question.items():
        unique_raters = {row["rater_id"] for row in rows}
        if len(unique_raters) < 2:
            continue
        multi_rater_items += 1
        values = {(row["evidence_state"], row["answer"]) for row in rows}
        if len(values) == 1:
            exact_agreement_items += 1
        else:
            disputed_items.append(qid)
    return {
        "profile_id": document["profile_id"],
        "reference_period": document["reference_period"],
        "ratings_count": len(ratings),
        "independent_raters": len({r["rater_id"] for r in ratings}),
        "evidence_states": dict(status_counts),
        "items_with_multiple_raters": multi_rater_items,
        "items_with_exact_agreement": exact_agreement_items,
        "items_with_disagreement": sorted(disputed_items),
        "note": "Descriptive exact agreement only, not inter-rater reliability/validity.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_file", type=Path)
    args = parser.parse_args()
    with args.evidence_file.open(encoding="utf-8") as stream:
        document = json.load(stream)
    print(json.dumps(summarize_audit(document), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
