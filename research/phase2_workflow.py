"""Research-readiness dashboard and immutable-item decision ledger.

Human review, cognitive interviews and ethics signoff are explicitly deferred.
Neither this tool nor its output can authorize collection.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
import json
from pathlib import Path

from research.assignment import load_instrument
from research.content_review import parse_reviews, summarize_reviews, verify_snapshot
from research.cognitive_review import load_interviews, summarize_interviews
from research.item_audit import audit_bank

COLUMNS=("instrument_version","language","item_id","axis_id","decision",
         "replacement_text","destination_axis","expert_evidence_refs",
         "cognitive_evidence_refs","rationale","editor_code","decision_date")
ACTIONS={"retain","revise","reassign","retire","discuss"}


def decision_template(path:Path):
    verify_snapshot()
    if path.exists():raise FileExistsError("Cannot overwrite decision ledger")
    bank=load_instrument()
    with path.open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=COLUMNS)
        w.writeheader()
        for lang in ("en","pt"):
            for item in bank["items"]:
                w.writerow({"instrument_version":bank["instrument_version"],"language":lang,
                            "item_id":item["id"],"axis_id":item["axis_id"]})


def validate_decisions(path:Path)->list[dict]:
    verify_snapshot()
    bank=load_instrument()
    source={i["id"]:i for i in bank["items"]}
    axes={a["id"] for a in bank["axes"]}
    recorded=[]
    seen=set()
    with path.open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        if set(reader.fieldnames or ())!=set(COLUMNS):raise ValueError("Decision ledger schema mismatch")
        for n,row in enumerate(reader,2):
            try:
                item=source[row["item_id"]]
                locale=row["language"]
                if locale not in ("en","pt") or row["axis_id"]!=item["axis_id"]:
                    raise ValueError("Item metadata mismatch")
                if row["instrument_version"]!=bank["instrument_version"]:
                    raise ValueError("Version mismatch")
                key=(locale,item["id"])
                if key in seen:raise ValueError("Duplicate item/locale")
                seen.add(key)
                if not any(row[field].strip() for field in COLUMNS[4:]):
                    continue # empty template != approval
                if row["decision"] not in ACTIONS:raise ValueError("Unknown decision")
                mandatory=("expert_evidence_refs","rationale","editor_code","decision_date")
                if any(not row[k].strip() for k in mandatory):
                    raise ValueError("Decision requires expert evidence reference and provenance")
                if row["decision"]=="revise" and not row["replacement_text"].strip():
                    raise ValueError("No revised wording")
                if row["decision"]!="revise" and row["replacement_text"].strip():
                    raise ValueError("Replacement text only allowed with revise")
                if row["decision"]=="reassign" and (
                     row["destination_axis"] not in axes or row["destination_axis"]==item["axis_id"]):
                    raise ValueError("Invalid reassignment")
                if row["decision"]!="reassign" and row["destination_axis"].strip():
                    raise ValueError("Destination only for reassign")
                if date.fromisoformat(row["decision_date"]).isoformat()!=row["decision_date"]:
                    raise ValueError("Invalid ISO date")
                recorded.append(row)
            except (KeyError,ValueError,TypeError,AttributeError) as exc:
                raise ValueError(f"{path}:{n}: {exc}") from exc
    return recorded


def readiness(review_files:list[Path]|None=None, interview_files:list[Path]|None=None,
              decisions:Path|None=None,min_experts:int=5)->dict:
    verify_snapshot()
    audit=audit_bank()
    expert=summarize_reviews(parse_reviews(review_files),min_raters=min_experts) \
        if review_files else summarize_reviews([],min_raters=min_experts)
    cognitive=summarize_interviews(load_interviews(interview_files)) \
        if interview_files else summarize_interviews([])
    entries=validate_decisions(decisions) if decisions else []
    gates={
        "locked_draft_intact":bool(audit["locked_git_blob_sha"]),
        "all_240_items_and_24_polarity_groups":audit["items"]==240 and
            len(audit["axis_polarity"])==24 and all(n==10 for n in audit["axis_polarity"].values()),
        "expert_en_240_complete":expert["coverage"]["en"]["items_with_min_raters"]==240,
        "expert_pt_240_complete":expert["coverage"]["pt"]["items_with_min_raters"]==240,
        "cognitive_en_240_observed_twice":cognitive["by_language"]["en"]["items_observed_twice"]==240,
        "cognitive_pt_240_observed_twice":cognitive["by_language"]["pt"]["items_observed_twice"]==240,
        "editorial_480_decisions":len(entries)==480,
        "no_unresolved_editorial_actions":bool(entries) and all(e["decision"] in ("retain","revise") for e in entries),
        "human_qualifications_and_ethics_approved":False,
        "privacy_and_security_signoff":False,
    }
    return {"instrument_version":audit["instrument_version"],
            "instrument_status":"NOT_APPROVED_FOR_FIELDING",
            "mechanical_flags":audit["flag_counts"],
            "review":expert["coverage"],
            "completed_expert_ratings":expert["reviewed_ratings"],
            "cognitive":cognitive["by_language"],
            "editorial":{"recorded":len(entries),"missing":480-len(entries),
                         "unresolved":sum(e["decision"] in ("reassign","retire","discuss") for e in entries)},
            "gates":gates,
            "can_collect_human_political_opinions":False,
            "next":"Expert reviews, cognitive interviews, real decisions and ethics/privacy signoffs explicitly deferred. No approved pilot is generated."}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review",nargs="*",type=Path,default=[])
    parser.add_argument("--interview",nargs="*",type=Path,default=[])
    parser.add_argument("--decisions",type=Path)
    parser.add_argument("--template",type=Path)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    if args.template:decision_template(args.template)
    report=readiness(args.review,args.interview,args.decisions)
    data=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
    if args.output:
        if args.output.exists():raise FileExistsError("Refusing overwrite")
        args.output.write_text(data,encoding="utf-8")
    else:print(data,end="")


if __name__=="__main__":main()
