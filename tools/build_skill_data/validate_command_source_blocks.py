"""Offline validation for manually recovered command source blocks."""
import hashlib
import json
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "skill_data"
PDF = ROOT / "Downloads" / "AS_166309_LJ-X8000_UM_N04GB_WW_GB_2036_1.pdf"
SHA = "e3e51b234b56ea11182e78b39574678f5c7244c65d6455664927f580dd1a47c3"
DOC = "KEYENCE-E3E51B234B56"

def digest(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
 return h.hexdigest()

def main():
 errors=[]; warnings=[]
 if not PDF.exists() or digest(PDF)!=SHA: errors.append("authoritative source PDF missing or SHA mismatch")
 page_count=len(fitz.open(PDF)) if PDF.exists() else 0
 registry=[json.loads(line) for line in (ROOT/"registry"/"source_registry.jsonl").read_text(encoding="utf8").splitlines()]
 source=next((x for x in registry if x.get("document_id")==DOC),None)
 if not source or source.get("sha256")!=SHA or Path(source.get("source_path","")).name!=PDF.name:
  errors.append("source registry does not identify the authoritative PDF and SHA")
 blocks={}
 for p in (OUT/"evidence"/"manual_source_blocks").glob("*.json"):
  x=json.loads(p.read_text(encoding="utf8")); blocks[x["block_id"]]=x
  if x["source_sha256"]!=SHA or not 1<=x["pdf_page_index"]<=page_count: errors.append(f"invalid source block: {p.name}")
 data=json.loads((OUT/"operations"/"command_reference.yaml").read_text(encoding="utf8"))
 by={x["command"]:x for x in data["commands"]}
 for cmd,x in by.items():
  if x.get("knowledge_status") in {"OFFICIAL_EXACT","PARTIALLY_EXACT"}:
   for e in x.get("direct_evidence",[]):
    if e.get("block_id") and e["block_id"] not in blocks: errors.append(f"{cmd}: dangling source block")
   request=x.get("request",{}).get("syntax")
   if isinstance(request,dict) and request.get("status")=="OFFICIAL_EXACT" and not request.get("evidence"): errors.append(f"{cmd}: exact syntax has no direct evidence")
 for cmd in ("PFR","PFRF"):
  if cmd not in by: errors.append(f"missing {cmd}")
 if by.get("PFR",{}).get("request",{}).get("syntax",{}).get("value")==by.get("PFRF",{}).get("request",{}).get("syntax",{}).get("value"): errors.append("PFR/PFRF request syntax conflated")
 for p in [OUT/"routing"/"command_index.json", OUT/"communication"/"ethernet_nonprocedural.yaml", OUT/"unresolved"/"command_review_queue.yaml"]:
  try: json.loads(p.read_text(encoding="utf8"))
  except Exception as exc: errors.append(f"invalid JSON/YAML {p.name}: {exc}")
 index=json.loads((OUT/"routing"/"command_index.json").read_text(encoding="utf8"))
 if {x["command"] for x in index}!={x["command"] for x in data["commands"]}: errors.append("command index does not resolve all canonical commands")
 matrix=json.loads((OUT/"communication"/"communication_matrix.yaml").read_text(encoding="utf8"))
 if not any(x.get("method")=="Ethernet Non-Procedural" and x.get("canonical_detail_reference")=="communication/ethernet_nonprocedural.yaml" for x in matrix.get("methods",[])):
  errors.append("communication matrix lacks canonical Ethernet Non-Procedural reference")
 report="# Command source-block validation\n\nErrors: %d. Warnings: %d. Source blocks: %d.\n"%(len(errors),len(warnings),len(blocks))
 if errors: report+="\n## Errors\n"+"\n".join(f"- {x}" for x in errors)+"\n"
 if warnings: report+="\n## Warnings\n"+"\n".join(f"- {x}" for x in warnings)+"\n"
 (OUT/"validation_command_source_blocks.md").write_text(report,encoding="utf8")
 print(json.dumps({"errors":errors,"warnings":warnings,"source_blocks":len(blocks)}))
 if errors: raise SystemExit(1)
if __name__=="__main__": main()
