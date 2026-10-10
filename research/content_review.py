"""Content-validity expert review tooling (offline, non-participant data only).

No evaluation is simulated. Results are descriptive, not proof of validity.
Write reviewer packets only to private paths; keep completed forms out of Git.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re

from research.assignment import DEFAULT_INSTRUMENT, load_instrument

COLUMNS = [
    "reviewer_id", "instrument_version", "language", "item_id", "axis_id",
    "agree_pole", "is_common_item", "question_text",
    "relevance_1to4", "clarity_1to4", "construct_fit_1to4",
    "leading_yes_no", "double_barrel_yes_no", "cross_cultural_risk_yes_no",
    "proposed_axis_id", "proposed_action", "evidence_note",
]
METRICS = ("relevance_1to4", "clarity_1to4", "construct_fit_1to4")
FLAGS = ("leading_yes_no", "double_barrel_yes_no", "cross_cultural_risk_yes_no")
ACTIONS = {"retain", "revise", "reassign", "retire", "discuss"}
REVIEWER_CODE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{1,63}\Z")


def verify_snapshot(instrument_path: Path = DEFAULT_INSTRUMENT) -> str:
    """Reject accidental edits to frozen draft questionnaire content."""
    lock_path = instrument_path.parent / "LOCK.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    raw = instrument_path.read_bytes()
    digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if digest != lock["snapshot_git_blob_sha"]:
        raise ValueError("Frozen instrument contents no longer match the Git blob lock")
    document = load_instrument(instrument_path)
    if document["instrument_version"] != lock["instrument_version"]:
        raise ValueError("Instrument version and lock disagree")
    return digest


def make_packet(reviewer_id: str, language: str, *, instrument_path: Path = DEFAULT_INSTRUMENT) -> list[dict]:
    verify_snapshot(instrument_path)
    if not REVIEWER_CODE.fullmatch(reviewer_id):
        raise ValueError("Use an anonymous reviewer code of 2–64 safe characters")
    if language not in ("en", "pt"):
        raise ValueError("Expert review supports en and pt, separately")
    instrument = load_instrument(instrument_path)
    common = set(instrument["assignment"]["common_ids"])
    rows = []
    for item in instrument["items"]:
        row = {
            "reviewer_id": reviewer_id,
            "instrument_version": instrument["instrument_version"],
            "language": language,
            "item_id": item["id"],
            "axis_id": item["axis_id"],
            "agree_pole": item["agree_pole"],
            "is_common_item": "yes" if item["id"] in common else "no",
            "question_text": item["wording"][language],
        }
        row.update({field: "" for field in COLUMNS if field not in row})
        rows.append(row)
    return rows


def _write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    if path.exists():
        raise FileExistsError("Refusing to overwrite existing review materials")
    if not path.parent.is_dir():
        raise FileNotFoundError("Create a private output directory first")
    with path.open("x", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_packet(path: Path, reviewer_id: str, language: str) -> None:
    _write_csv(path, COLUMNS, make_packet(reviewer_id, language))


def parse_reviews(files: list[Path], *, instrument_path: Path = DEFAULT_INSTRUMENT) -> list[dict]:
    verify_snapshot(instrument_path)
    instrument = load_instrument(instrument_path)
    by_id = {i["id"]: i for i in instrument["items"]}
    seen = set()
    scored = []
    for filepath in files:
        with filepath.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or set(reader.fieldnames) != set(COLUMNS):
                raise ValueError(f"{filepath}: incorrect or incomplete review columns")
            for number, row in enumerate(reader, 2):
                try:
                    reviewer = row["reviewer_id"]
                    item_id = row["item_id"]
                    language = row["language"]
                    if not REVIEWER_CODE.fullmatch(reviewer) or language not in ("pt", "en"):
                        raise ValueError("reviewer id or locale invalid")
                    item = by_id[item_id]
                    expected = (instrument["instrument_version"], item["axis_id"],
                                item["agree_pole"], item["wording"][language])
                    actual = (row["instrument_version"], row["axis_id"],
                              row["agree_pole"], row["question_text"])
                    if actual != expected:
                        raise ValueError("question text, axis or instrument changed")
                    is_common = "yes" if item_id in instrument["assignment"]["common_ids"] else "no"
                    if row["is_common_item"] != is_common:
                        raise ValueError("common-item membership altered")
                    key = (reviewer, language, item_id)
                    if key in seen:
                        raise ValueError("duplicate reviewer/locale/item submission")
                    seen.add(key)
                    if not any(row[field].strip() for field in METRICS + FLAGS +
                               ("proposed_axis_id", "proposed_action", "evidence_note")):
                        continue  # blank, not an expert rating
                    if any(row[field] not in {"1", "2", "3", "4"} for field in METRICS):
                        raise ValueError("all three independent 1–4 ratings required")
                    if any(row[field] not in {"", "yes", "no"} for field in FLAGS):
                        raise ValueError("risk flags must be yes, no, or blank")
                    if row["proposed_axis_id"] and row["proposed_axis_id"] not in {
                            a["id"] for a in instrument["axes"]}:
                        raise ValueError("unknown proposed axis")
                    if row["proposed_action"] and row["proposed_action"] not in ACTIONS:
                        raise ValueError("unknown suggested action")
                    scored.append(row)
                except (KeyError, TypeError, AttributeError, ValueError) as exc:
                    raise ValueError(f"{filepath}:{number}: {exc}") from exc
    return scored


def summarize_reviews(rows: list[dict], *, instrument_path: Path = DEFAULT_INSTRUMENT,
                      min_raters: int = 5) -> dict:
    """Descriptive I-CVI; no unreviewed item is treated as passing any threshold."""
    if min_raters < 2:
        raise ValueError("min_raters must be >=2")
    instrument = load_instrument(instrument_path)
    groups = defaultdict(list)
    for row in rows:
        groups[(row["language"], row["item_id"])].append(row)
    items = []
    for (locale, iid), reviews in sorted(groups.items()):
        reviewers = {row["reviewer_id"] for row in reviews}
        if len(reviewers) != len(reviews):
            raise ValueError("more than one rating per reviewer in a group")
        ratings = len(reviews)
        item = next(i for i in instrument["items"] if i["id"] == iid)
        score = sum(int(row["relevance_1to4"]) >= 3 for row in reviews) / ratings
        clarity = sum(int(row["clarity_1to4"]) >= 3 for row in reviews) / ratings
        fit = sum(int(row["construct_fit_1to4"]) >= 3 for row in reviews) / ratings
        risk = {flag: sum(row[flag] == "yes" for row in reviews) for flag in FLAGS}
        items.append({
            "language": locale, "item_id": iid, "axis_id": item["axis_id"],
            "ratings_n": ratings,
            "i_cvi_relevance": round(score, 4),
            "proportion_clear": round(clarity, 4),
            "proportion_construct_fit": round(fit, 4),
            "risk_yes_counts": risk,
            "suggested_actions": dict(Counter(r["proposed_action"] for r in reviews
                                              if r["proposed_action"])),
            "adequate_review_coverage": ratings >= min_raters,
            "requires_discussion": ratings < min_raters or score < .78 or
              any(n > 0 for n in risk.values()) or
              any(r["proposed_action"] in {"revise", "reassign", "retire", "discuss"} for r in reviews),
        })
    coverage = {lang: {
        "items_with_any_review": sum(item["language"] == lang for item in items),
        "items_with_min_raters": sum(item["language"] == lang and item["adequate_review_coverage"]
                                     for item in items),
    } for lang in ("en", "pt")}
    for locale in ("en", "pt"):
        relevant = [item["i_cvi_relevance"] for item in items if item["language"] == locale
                    and item["adequate_review_coverage"]]
        coverage[locale]["s_cvi_ave_expert_reviewed_only"] = (round(sum(relevant)/len(relevant), 4)
                                                              if len(relevant) == 240 else None)
    return {
        "instrument_version": instrument["instrument_version"],
        "reviewed_ratings": len(rows),
        "unique_reviewer_codes": len({r["reviewer_id"] for r in rows}),
        "min_raters_for_coverage": min_raters,
        "coverage": coverage,
        "items": items,
        "methodology_warning": "Descriptive judgments only. .78 is an optional review-discussion flag, not a statistical proof or mandatory accept/reject rule. S-CVI/Ave withheld until all 240 items in that language have adequate expert coverage. Do not mix PT and EN assessments or treat expert ratings as participant data.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    packet = commands.add_parser("packet", help="Create a blank, immutable-question expert review CSV")
    packet.add_argument("--reviewer", required=True)
    packet.add_argument("--lang", choices=("en", "pt"), required=True)
    packet.add_argument("--output", type=Path, required=True)
    report = commands.add_parser("report", help="Summarize completed expert CSVs (private)")
    report.add_argument("--min-raters", type=int, default=5)
    report.add_argument("--output", type=Path, required=True)
    report.add_argument("files", type=Path, nargs="+")
    args = parser.parse_args()
    if args.mode == "packet":
        write_packet(args.output, args.reviewer, args.lang)
        print(f"Created {args.output}; expert ratings remain blank")
    else:
        results = summarize_reviews(parse_reviews(args.files), min_raters=args.min_raters)
        if args.output.exists():
            raise FileExistsError("Refusing to overwrite previous expert assessment")
        args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Summarized {results['reviewed_ratings']} independently entered assessments")


if __name__ == "__main__":
    main()
