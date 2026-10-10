"""Deterministic, non-scientific item wording diagnostics on the locked draft."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from research.assignment import DEFAULT_INSTRUMENT, load_instrument
from research.content_review import verify_snapshot


def tokens(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", text).casefold()))


def audit_bank(instrument_path: Path = DEFAULT_INSTRUMENT) -> dict:
    locked = verify_snapshot(instrument_path)
    bank = load_instrument(instrument_path)
    core = set(bank["assignment"]["common_ids"])
    tally = Counter((i["axis_id"], i["agree_pole"]) for i in bank["items"])
    rows = []
    for lang in ("en","pt"):
        seen = defaultdict(list)
        bag = {}
        for item in bank["items"]:
            words = tokens(item["wording"][lang])
            bag[item["id"]] = set(words)
            seen[" ".join(words)].append(item["id"])
            flags = []
            if len(words) < 7: flags.append("SHORT_TEXT_HEURISTIC")
            if len(words) > 45: flags.append("LONG_TEXT_HEURISTIC")
            if len(item["wording"][lang]) > 350: flags.append("LONG_CHARACTERS_HEURISTIC")
            other = "pt" if lang == "en" else "en"
            if words == tokens(item["wording"][other]): flags.append("IDENTICAL_TRANSLATION_TEXT")
            rows.append({"language":lang, "item_id":item["id"],"axis_id":item["axis_id"],
                         "agree_pole":item["agree_pole"],"common":item["id"] in core,
                         "word_count":len(words), "flags":flags})
        duplicated = {iid for ids in seen.values() if len(ids) > 1 for iid in ids}
        for entry in rows:
            if entry["language"] == lang and entry["item_id"] in duplicated:
                entry["flags"].append("EXACT_DUPLICATE_TEXT")
        # Same-axis lexical overlap indicates possible redundancy, not semantic identity.
        for axis in bank["axes"]:
            ids = [i["id"] for i in bank["items"] if i["axis_id"]==axis["id"]]
            for pos,a in enumerate(ids):
                for b in ids[pos+1:]:
                    if min(len(bag[a]),len(bag[b])) < 7: continue
                    if len(bag[a]&bag[b])/len(bag[a]|bag[b]) >= 0.86:
                        for entry in rows:
                            if entry["language"] == lang and entry["item_id"] in (a,b):
                                if "HIGH_LEXICAL_OVERLAP" not in entry["flags"]:
                                    entry["flags"].append("HIGH_LEXICAL_OVERLAP")
    return {
        "instrument_version":bank["instrument_version"],
        "locked_git_blob_sha":locked,
        "items":len(bank["items"]), "language_item_rows":len(rows), "core_items":len(core),
        "axis_polarity":{f"{a['id']}:{pole}":tally[(a["id"],pole)]
                         for a in bank["axes"] for pole in ("LEFT","RIGHT")},
        "flag_counts":dict(Counter(f for entry in rows for f in set(entry["flags"]))),
        "diagnostics":rows,
        "warning":"These are lexical heuristics, NOT subject matter findings. Zero flags does not imply validity or translation equivalence."
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    report=audit_bank()
    if args.output:
        if args.output.exists(): raise FileExistsError("Refusing overwrite")
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(f"Prepared {report['language_item_rows']} mechanical diagnostics")
    else:
        print(json.dumps({k:v for k,v in report.items() if k!="diagnostics"},indent=2,ensure_ascii=False))


if __name__=="__main__": main()
