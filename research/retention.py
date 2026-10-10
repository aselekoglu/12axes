"""Expire old sessions in an approved private research environment.

Backup copies/exports are NOT purged by this script; operators must independently
verify retention rules across backups, exports, logs and replicas.
"""
from __future__ import annotations

import argparse
import os

from research.service import _connect


def expire(*, execute: bool = False, connector=None) -> int:
    if execute and os.getenv("RESEARCH_RETENTION_DELETE_ACKNOWLEDGE") != "DELETE_EXPIRED_LOCAL_RECORDS":
        raise PermissionError("Set explicit retention delete acknowledgment to execute")
    connector = connector or _connect
    with connector() as conn:
        with conn.cursor() as cur:
            if execute:
                cur.execute("DELETE FROM research_sessions WHERE expires_at < now()")
                return cur.rowcount
            cur.execute("SELECT count(*) AS n FROM research_sessions WHERE expires_at < now()")
            return cur.fetchone()["n"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Execute deletion after policy approval")
    args = parser.parse_args()
    count = expire(execute=args.execute)
    print(f"{'Deleted' if args.execute else 'Would delete'} {count} expired research session records.")
    if args.execute:
        print("Ensure backup, replica and restricted CSV export retention separately.")


if __name__ == "__main__":
    main()
