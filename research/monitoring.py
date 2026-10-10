"""Aggregate-only operations reporting, not an HTTP endpoint or public dashboard."""
from __future__ import annotations

import argparse
import json

from research.service import _connect, _fielding_settings


def summarize(instrument_version: str | None = None, connector=None) -> dict:
    if instrument_version is None:
        instrument, _, _ = _fielding_settings()
        instrument_version = instrument["instrument_version"]
    connector = connector or _connect
    with connector() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT count(*) AS assigned,
                 count(*) FILTER (WHERE completed_at IS NOT NULL) AS completed,
                 count(*) FILTER (WHERE completed_at IS NULL) AS incomplete,
                 count(*) FILTER (WHERE expires_at <= now()) AS expired
                 FROM research_sessions WHERE instrument_version = %s""", (instrument_version,))
            stats = dict(cur.fetchone())
            cur.execute("""SELECT language, count(*) AS assigned,
                 count(*) FILTER (WHERE completed_at IS NOT NULL) AS completed
                 FROM research_sessions WHERE instrument_version = %s
                 GROUP BY language ORDER BY language""", (instrument_version,))
            language = [dict(row) for row in cur.fetchall()]
            cur.execute("""SELECT assigned.question_id, count(*) AS assigned_count
                 FROM research_sessions AS s
                 CROSS JOIN LATERAL unnest(s.assigned_ids) AS assigned(question_id)
                 WHERE s.instrument_version = %s GROUP BY assigned.question_id""",
                        (instrument_version,))
            coverage = {row["question_id"]: row["assigned_count"] for row in cur.fetchall()}
            cur.execute("""SELECT response.key AS question_id, count(*) AS completed_count
                 FROM research_sessions AS s
                 CROSS JOIN LATERAL jsonb_each(s.answers) AS response(key, value)
                 WHERE s.instrument_version = %s AND s.completed_at IS NOT NULL
                 GROUP BY response.key""", (instrument_version,))
            observed = {row["question_id"]: row["completed_count"] for row in cur.fetchall()}
    return {
        "instrument_version": instrument_version,
        "sessions": stats,
        "by_language": language,
        "item_assignment_count": coverage,
        "item_completed_response_count": observed,
        "warning": "Aggregate research operations only; incomplete sessions have no partial answers. Not a validity statistic, not representative, and not public data.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print aggregate counts only")
    args = parser.parse_args()
    if not args.json:
        parser.error("Specify --json to acknowledge aggregate metrics output")
    print(json.dumps(summarize(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
