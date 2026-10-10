"""Validate private human-entered cognitive interview observations.

A generated moderator packet is NOT a completed interview or evidence.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re
from research.cognitive_packets import make_interview_packet
from research.content_review import verify_snapshot

FIELDS=("interview_id","round_id","language","packet_index","item_id",
        "comprehension","retrieval","judgment","response_mapping",
        "severity","observation","suggested_action")
DOMAINS=("comprehension","retrieval","judgment","response_mapping")
VALUES={"not_observed","issue_observed","not_assessed"}
SEVERITY={"none","minor","moderate","severe","not_assessed"}
ACTIONS={"retain","revise","reassign","retire","discuss","no_action"}
ID_PATTERN=re.compile(r"[A-Za-z0-9_-]{3,64}\Z")


def make_template(path:Path, code:str, index:int, lang:str="en", round_id:str="draft-round-1"):
    if path.exists(): raise FileExistsError("Refusing overwrite")
    if not ID_PATTERN.fullmatch(code): raise ValueError("Pseudonymous interview code required")
    assigned=make_interview_packet(index,lang,round_id=round_id)
    with path.open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS)
        writer.writeheader()
        for item in assigned:
            writer.writerow({"interview_id":code,"round_id":round_id,"language":lang,
                             "packet_index":index,"item_id":item["item_id"]})


def load_interviews(paths:list[Path])->list[dict]:
    verify_snapshot()
    seen=set()
    assignments={}
    collected=[]
    for path in paths:
        with path.open(newline="",encoding="utf-8-sig") as f:
            reader=csv.DictReader(f)
            if set(reader.fieldnames or ())!=set(FIELDS): raise ValueError("Interview schema mismatch")
            for n,row in enumerate(reader,2):
                try:
                    code=row["interview_id"]
                    if not ID_PATTERN.fullmatch(code): raise ValueError("Invalid interviewer code")
                    lang,ix,round_id=row["language"],int(row["packet_index"]),row["round_id"]
                    packet=make_interview_packet(ix,lang,round_id=round_id)
                    allowed={i["item_id"] for i in packet}
                    if row["item_id"] not in allowed: raise ValueError("Item not in participant allocation")
                    context=(lang,ix,round_id)
                    if code in assignments and assignments[code]!=context:
                        raise ValueError("Interview code spans multiple allocations")
                    assignments[code]=context
                    key=(code,row["item_id"])
                    if key in seen: raise ValueError("Duplicate coded item")
                    seen.add(key)
                    if not any(row[k].strip() for k in FIELDS[5:]):
                        continue  # blank packet is NOT interview evidence
                    if any(row[d] not in VALUES for d in DOMAINS): raise ValueError("Uncoded probe")
                    if row["severity"] not in SEVERITY or row["suggested_action"] not in ACTIONS:
                        raise ValueError("Invalid severity/action")
                    issue=any(row[d]=="issue_observed" for d in DOMAINS)
                    if issue and (row["severity"] in ("none","not_assessed") or not row["observation"].strip()):
                        raise ValueError("Issue needs severity and observation")
                    if not issue and row["severity"] not in ("none","not_assessed"):
                        raise ValueError("Severity without issue")
                    collected.append(row)
                except (KeyError,ValueError,TypeError) as exc:
                    raise ValueError(f"{path}:{n}: {exc}") from exc
    return collected


def summarize_interviews(rows:list[dict])->dict:
    counts=Counter((r["language"],r["item_id"]) for r in rows)
    issues=Counter((r["language"],r["item_id"]) for r in rows
                   if any(r[d]=="issue_observed" for d in DOMAINS))
    return {"completed_item_probes":len(rows),
            "by_language":{lang:{
                "interviews_with_completed_probes":len({r["interview_id"] for r in rows if r["language"]==lang}),
                "items_with_observation":sum(k[0]==lang for k in counts),
                "items_observed_twice":sum(k[0]==lang and n>=2 for k,n in counts.items()),
                "items_with_issues":sum(k[0]==lang for k in issues),
            } for lang in ("en","pt")},
            "issues":[{"language":lang,"item_id":qid,"count":n}
                      for (lang,qid),n in sorted(issues.items())],
            "warning":"Recorded observations are not a psychometric validation; two appearances do not prove universal comprehension."}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    template=sub.add_parser("template")
    template.add_argument("--interview",required=True)
    template.add_argument("--index",required=True,type=int)
    template.add_argument("--lang",choices=("en","pt"),default="en")
    template.add_argument("--round",dest="round_id",default="draft-round-1")
    template.add_argument("--output",required=True,type=Path)
    report=sub.add_parser("report")
    report.add_argument("--output",required=True,type=Path)
    report.add_argument("files",nargs="+",type=Path)
    args=parser.parse_args()
    if args.command=="template":
        make_template(args.output,args.interview,args.index,args.lang,args.round_id)
    else:
        data=summarize_interviews(load_interviews(args.files))
        if args.output.exists():raise FileExistsError("Refusing overwrite")
        args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
        print(f"Coded {data['completed_item_probes']} observations")


if __name__=="__main__":main()
