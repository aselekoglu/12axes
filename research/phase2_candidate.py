"""Compile an *unapproved* candidate snapshot after genuine Phase 2 review.

This tool cannot create an approved pilot; it checks review coverage, provenance
and 480 complete editorial decisions and still sets NOT_APPROVED_FOR_FIELDING.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from research.assignment import load_instrument
from research.phase2_workflow import readiness, validate_decisions


def compile_candidate(decisions_file:Path, expert_files:list[Path],
                      interview_files:list[Path], destination:Path, min_experts:int=5)->dict:
    if destination.exists():raise FileExistsError("Refusing to overwrite an instrument proposal")
    gate=readiness(expert_files,interview_files,decisions_file,min_experts)
    technical=gate["gates"]
    required=("locked_draft_intact","all_240_items_and_24_polarity_groups",
              "expert_en_240_complete","expert_pt_240_complete",
              "cognitive_en_240_observed_twice","cognitive_pt_240_observed_twice",
              "editorial_480_decisions","no_unresolved_editorial_actions")
    missing=[key for key in required if not technical[key]]
    if missing:
        raise ValueError("Cannot build candidate: missing review evidence or unresolved changes: "+
                         ", ".join(missing))
    decisions=validate_decisions(decisions_file)
    bank=copy.deepcopy(load_instrument())
    lookup={item["id"]:item for item in bank["items"]}
    for row in decisions:
        if row["decision"]=="revise":
            lookup[row["item_id"]]["wording"][row["language"]]=row["replacement_text"]
    # Deliberately impossible to load for fielding through research.assignment.
    bank["instrument_version"]="candidate-0.1"
    bank["research_status"]="NOT_APPROVED_FOR_FIELDING"
    bank["scientific_validation_status"]="NOT_VALIDATED"
    bank["release_gate"]="HUMAN_EXPERT_AND_ETHICS_SIGNOFF_REQUIRED"
    bank["phase2_provenance"]={
        "source_version":gate["instrument_version"],
        "reviewed_decision_count":len(decisions),
        "decision_csv_sha256":hashlib.sha256(decisions_file.read_bytes()).hexdigest(),
        "expert_input_sha256":{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in expert_files},
        "interview_input_sha256":{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in interview_files},
        "warning":"Evidence file digests are provenance hints, not authentication of expert identity."
    }
    destination.write_text(json.dumps(bank,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"path":str(destination),"version":bank["instrument_version"],
            "status":bank["research_status"],"fielding":False,
            "warning":"Candidate has not received independent ethics/privacy approval and cannot be used in the live study."}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions",required=True,type=Path)
    parser.add_argument("--experts",required=True,nargs="+",type=Path)
    parser.add_argument("--interviews",required=True,nargs="+",type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(compile_candidate(args.decisions,args.experts,args.interviews,args.output),indent=2))


if __name__=="__main__": main()
