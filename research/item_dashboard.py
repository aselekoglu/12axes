"""Generate a private, offline, static audit browser for the 240 draft questions.

No external resources, network calls, reviewer records or participant data.
"""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path

from research.assignment import load_instrument
from research.item_audit import audit_bank

DOC = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>12Axes | Question audit (mechanical only)</title>
<style>
:root{color-scheme:light dark;font-family:system-ui,-apple-system,sans-serif}
body{max-width:1100px;margin:auto;padding:24px;background:Canvas;color:CanvasText}
header{display:flex;justify-content:space-between;flex-wrap:wrap;gap:20px;align-items:center}
h1{letter-spacing:-.04em;line-height:1.1}p{line-height:1.6;max-width:850px}
.warning{border:1px solid #a2772e;border-radius:12px;padding:16px;margin:16px 0}
.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:end;margin:20px 0}
label{display:flex;flex-direction:column;gap:6px;font-size:.84rem}
input,select{padding:9px;border-radius:7px;border:1px solid GrayText;background:Canvas;color:CanvasText}
input[type=checkbox]{margin-right:7px}
.tablewrap{overflow:auto;border-radius:12px;border:1px solid GrayText}
table{border-collapse:collapse;min-width:800px;width:100%}
th,td{padding:12px 10px;text-align:left;vertical-align:top;border-bottom:1px solid GrayText}
th{background:ButtonFace;position:sticky;top:0}
td:first-child{white-space:nowrap;font-family:monospace}
.flag{display:inline-block;border:1px solid GrayText;border-radius:12px;padding:3px 6px;margin:2px;font-size:.71rem}
small{opacity:.8} #count{font-weight:700} .pill{padding:5px 10px;border:1px solid GrayText;border-radius:20px}
footer{margin-top:25px}
</style></head><body>
<header><div><small>12AXES / SCIENTIFIC VALIDATION / PHASE 2</small><h1>Item-bank review queue</h1></div><span class="pill">NOT VALIDATED</span></header>
<p class="warning"><strong>Mechanical diagnostics only.</strong> Lexical or translation flags are clues for humans, not expert ratings, cognitive interview results, evidence of bias, scientific validity or permission to collect political opinions. The draft item bank is immutable.</p>
<div class="controls">
<label>Language<select id="lang"><option value="en">English</option><option value="pt">Português</option></select></label>
<label>Axis<select id="axis"><option value="">All axes</option></select></label>
<label>Search item or text<input id="query" type="search" placeholder="Search 240 questions"></label>
<label><span>Filter</span><span><input type="checkbox" id="flags">Flags only</span></label>
<label><span>Filter</span><span><input type="checkbox" id="core">Core 72 only</span></label>
</div>
<p id="count" aria-live="polite"></p>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Axis / polarity</th><th>Question text</th><th>Mechanical flags</th></tr></thead><tbody id="rows"></tbody></table></div>
<footer><small>Runs fully offline; no responses or expert observations are stored, sent or fabricated.</small></footer>
<script type="application/json" id="bank-data">__DATA__</script>
<script>
const data=JSON.parse(document.getElementById('bank-data').textContent);
const lang=document.getElementById('lang'),axis=document.getElementById('axis');
const query=document.getElementById('query'),flags=document.getElementById('flags'),core=document.getElementById('core');
const tbody=document.getElementById('rows');
for(const item of data.axes){const opt=document.createElement('option');opt.value=item.id;opt.textContent=item.label;axis.append(opt)}
function td(row,value){const cell=document.createElement('td');cell.textContent=value;row.append(cell);return cell}
function render(){
 const search=query.value.toLocaleLowerCase();
 tbody.replaceChildren();
 let count=0;
 const fragment=document.createDocumentFragment();
 for(const item of data.items){
  const diagnostic=data.flags[item.id+':'+lang.value];
  const words=item.wording[lang.value];
  if(axis.value&&item.axis_id!==axis.value)continue;
  if(flags.checked&&!diagnostic.length)continue;
  if(core.checked&&!item.core)continue;
  if(search&&!((item.id+' '+words+' '+item.axis_id).toLocaleLowerCase().includes(search)))continue;
  const row=document.createElement('tr');
  td(row,item.id+(item.core?' ★':''));
  td(row,item.axis_id+' / '+item.agree_pole);
  td(row,words);
  const cell=td(row,'');
  for(const code of diagnostic){const tag=document.createElement('span');tag.className='flag';tag.textContent=code;cell.append(tag)}
  fragment.append(row);count++;
 }
 tbody.append(fragment);
 document.getElementById('count').textContent=count+' of 240 questions shown ('+lang.value+')';
}
for(const el of [lang,axis,query,flags,core])el.addEventListener('input',render);
render();
</script></body></html>
"""


def build_dashboard(destination: Path) -> dict:
    if destination.exists():
        raise FileExistsError("Dashboard output already exists")
    bank=load_instrument()
    report=audit_bank()
    core=set(bank["assignment"]["common_ids"])
    diagnostics={(r["item_id"],r["language"]):r["flags"] for r in report["diagnostics"]}
    payload={
        "axes":[{"id":a["id"],"label":a["label"]} for a in bank["axes"]],
        "items":[{"id":it["id"],"axis_id":it["axis_id"],"agree_pole":it["agree_pole"],
                  "core":it["id"] in core,"wording":it["wording"]} for it in bank["items"]],
        "flags":{item["id"]+":"+lang:diagnostics[(item["id"],lang)]
                 for item in bank["items"] for lang in ("en","pt")},
    }
    serialized=json.dumps(payload,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")
    html=DOC.replace("__DATA__",serialized)
    destination.write_text(html,encoding="utf-8")
    return {"output":str(destination),"items":len(payload["items"]),
            "languages":2,"flag_counts":report["flag_counts"],
            "warning":"For private visual review only; not scientific validity"}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(build_dashboard(args.output),indent=2,ensure_ascii=False))


if __name__=="__main__":main()
