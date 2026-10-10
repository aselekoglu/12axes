"""Generate explicitly labeled, fictional response data for pipeline smoke tests.

This tool does not model a real political population or validate the 12 axes.
Its CSVs must never be mixed into real research data.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
import random

from research.assignment import load_instrument, generate_form

VALUES = ["STRONGLY_DISAGREE", "DISAGREE", "NEUTRAL", "AGREE", "STRONGLY_AGREE"]


def _choice(position: float) -> str:
    if position < -1.5:
        return VALUES[0]
    if position < -0.5:
        return VALUES[1]
    if position < 0.5:
        return VALUES[2]
    if position < 1.5:
        return VALUES[3]
    return VALUES[4]


def simulate(destination: Path, *, participants: int = 800, seed: int = 20261010,
             completion: float = 0.85) -> dict:
    if participants < 7 or participants > 10000:
        raise ValueError("Synthetic sample size must be between 7 and 10000")
    if not 0 <= completion <= 1:
        raise ValueError("completion must be between 0 and 1")
    if destination.exists():
        raise FileExistsError("Synthetic output directory must not exist")
    instrument = load_instrument()
    index = {item["id"]: item for item in instrument["items"]}
    rng = random.Random(seed)
    rows = {"participants.csv": [], "assignments.csv": [],
            "answers.csv": [], "archetypes.csv": []}
    for i in range(participants):
        # Obvious fake IDs; do not infer any scientific factor structure.
        person = f"FAKE_SYNTHETIC_{i:07d}"
        language = ("en", "pt")[i % 2]
        split = ("efa", "cfa")[i % 2]
        done = rng.random() < completion
        rows["participants.csv"].append([person, language, split, int(done),
                                         instrument["instrument_version"]])
        form = generate_form(i, instrument, study_seed=f"synthetic:{seed}")
        general = rng.gauss(0, 1)
        axis_signal = {axis["id"]: rng.gauss(0, 0.85) + general * 0.35
                       for axis in instrument["axes"]}
        for qid in form["question_ids"]:
            question = index[qid]
            rows["assignments.csv"].append([person, qid, question["axis_id"],
                         question["agree_pole"], int(done), int(done)])
            if done:
                direction = 1 if question["agree_pole"] == "LEFT" else -1
                v = axis_signal[question["axis_id"]] * direction + rng.gauss(0, 0.8)
                rows["answers.csv"].append([person, qid, question["axis_id"],
                                           question["agree_pole"], _choice(v), language])
        if done:
            for question in instrument["archetype_questions"]:
                option = rng.choice(question["options"])
                rows["archetypes.csv"].append([person, question["id"], option["id"]])

    headers = {
        "participants.csv": ["participant_id", "language", "split", "completed", "instrument_version"],
        "assignments.csv": ["participant_id", "question_id", "axis_id", "agree_pole", "completed", "answered"],
        "answers.csv": ["participant_id", "question_id", "axis_id", "agree_pole", "response", "language"],
        "archetypes.csv": ["participant_id", "question_id", "response"],
    }
    destination.mkdir(mode=0o700, parents=False, exist_ok=False)
    (destination / "SYNTHETIC_TEST_DATA_ONLY").write_text(
        "These are artificial, simulated answers; not evidence for scientific validation.\n",
        encoding="utf-8")
    for filename, values in rows.items():
        with (destination / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers[filename])
            writer.writerows(values)
    return {"participants": participants, "completed": sum(x[3] for x in rows["participants.csv"]),
            "assigned_rows": len(rows["assignments.csv"]),
            "answer_rows": len(rows["answers.csv"]),
            "instrument_version": instrument["instrument_version"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--participants", type=int, default=800)
    parser.add_argument("--seed", type=int, default=20261010)
    args = parser.parse_args()
    print(simulate(args.output_dir, participants=args.participants, seed=args.seed))


if __name__ == "__main__":
    main()
