"""Offline restricted export of sensitive research responses.

Run only inside an approved research environment. Data are pseudonymized,
NOT anonymous. Never upload the files to public artifacts or GitHub.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import os
from pathlib import Path

from research.service import _connect, _fielding_settings


def export_data(directory: Path) -> dict[str, int]:
    instrument, _, _ = _fielding_settings()
    if os.getenv("RESEARCH_EXPORT_ACKNOWLEDGE") != "I_HAVE_EXPORT_AUTHORIZATION":
        raise RuntimeError("Explicit export authorization is required")
    key = os.getenv("RESEARCH_EXPORT_KEY", "")
    if len(key) < 32:
        raise RuntimeError("RESEARCH_EXPORT_KEY must be at least 32 characters")
    if directory.exists():
        raise FileExistsError("Choose a new empty directory; refusing to overwrite export")
    directory.mkdir(mode=0o700, parents=False, exist_ok=False)
    os.chmod(directory, 0o700)

    lookup = {q["id"]: q for q in instrument["items"]}
    rows = {"assignments.csv": [], "answers.csv": [], "archetypes.csv": [], "participants.csv": []}
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT token_hash, form_index, instrument_version,
                                  language, assigned_ids, answers, archetype_answers,
                                  completed_at
                           FROM research_sessions
                           WHERE expires_at > now() ORDER BY form_index""")
            for session in cur:
                if session["instrument_version"] != instrument["instrument_version"]:
                    raise RuntimeError("Unexpected mixed instrument version; stop export")
                pseudonym = hmac.new(key.encode("utf-8"),
                    session["token_hash"].encode("ascii"), hashlib.sha256).hexdigest()[:24]
                completed = session["completed_at"] is not None
                # Stable, seeded held-out split; assign only AFTER eligibility gates.
                split_digest = hmac.new(key.encode("utf-8"),
                    ("split:" + pseudonym).encode("utf-8"), hashlib.sha256).digest()
                split = "efa" if int.from_bytes(split_digest[:8], "big") < 2**63 else "cfa"
                rows["participants.csv"].append([pseudonym, session["language"], split,
                                                  int(completed), session["instrument_version"]])
                for qid in session["assigned_ids"]:
                    if qid not in lookup:
                        raise RuntimeError("Unknown assigned item detected; stop export")
                    item = lookup[qid]
                    answer = (session["answers"] or {}).get(qid)
                    rows["assignments.csv"].append([pseudonym, qid, item["axis_id"],
                        item["agree_pole"], int(completed), int(answer is not None)])
                    if answer is not None:
                        rows["answers.csv"].append([pseudonym, qid, item["axis_id"],
                            item["agree_pole"], answer, session["language"]])
                for qid, value in (session["archetype_answers"] or {}).items():
                    rows["archetypes.csv"].append([pseudonym, qid, value])

    headers = {
        "participants.csv": ["participant_id", "language", "split", "completed", "instrument_version"],
        "assignments.csv": ["participant_id", "question_id", "axis_id", "agree_pole", "completed", "answered"],
        "answers.csv": ["participant_id", "question_id", "axis_id", "agree_pole", "response", "language"],
        "archetypes.csv": ["participant_id", "question_id", "response"],
    }
    for filename, values in rows.items():
        path = directory / filename
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(headers[filename])
            writer.writerows(values)
    return {name: len(values) for name, values in rows.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path, help="new private, nonexisting directory")
    args = parser.parse_args()
    summary = export_data(args.output_dir)
    print("Restricted local export completed. Sensitive pseudonymized data; do not publish.")
    for name, count in summary.items():
        print(f"{name}: {count} rows")


if __name__ == "__main__":
    main()
